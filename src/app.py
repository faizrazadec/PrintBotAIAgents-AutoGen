"""This module implements a Flask application with AutoGen and Socket.IO for real-time chat."""

import os
from typing import Union, Any

from flask import (
    Flask, 
    render_template
)
from flask_socketio import (
    SocketIO,
    emit
)
from autogen import (
    ConversableAgent,
    register_function,
    GroupChatManager,
    Agent,
    GroupChat
)
from dotenv import load_dotenv

from prompts import (
    system_prompt_assistant
)
from functions import (
    filter_products_by_category,
    get_product_info_by_reference,
    fetch_pricing_info
)
from logger import setup_logger

load_dotenv()
logger = setup_logger()
app = Flask(__name__)
socket_io = SocketIO(app, cors_allowed_origins="*")

def new_print_received_message(self, message: Union[dict[str, Any], str], sender):
    """Patches the GroupChatManager to emit messages via Socket.IO."""
    message = self._message_to_dict(message)
    message_content = message.get("content", "")

    if (
        sender.name == "assistant_agent" and not message_content
    ) or sender.name == "executor_agent":
        print(f"Filtered out: Sender={sender.name}, Content={message_content}")
        return

    print(f"PATCHED: Sender={sender.name}, Content={message_content}")
    socket_io.emit("message", {"sender": sender.name, "content": message_content})

GroupChatManager._print_received_message = new_print_received_message   # pylint: disable=W0212

llm_config = {
    "config_list": [
        {
            "api_type": "openai",
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    ],
}

executor_agent = ConversableAgent(
    name="executor_agent",
    human_input_mode="NEVER",
    system_message="You are the executor agent. Your role is to execute function calls and provide the results to the assistant agent.",
)

assistant = ConversableAgent(
    name="assistant_agent",
    llm_config=llm_config,
    system_message=system_prompt_assistant,
    human_input_mode="NEVER",
    functions=[filter_products_by_category, get_product_info_by_reference, fetch_pricing_info],
)

register_function(
    filter_products_by_category,
    caller=assistant,
    executor=executor_agent,
    description="Fetches products based on the given category name and returned to the assistant agent.",
)

register_function(
    get_product_info_by_reference,
    caller=assistant,
    executor=executor_agent,
    description="Gets detailed information about a product using its reference and return to the assistant agent.",
)

register_function(
    fetch_pricing_info,
    caller=assistant,
    executor=executor_agent,
    description="Fetches pricing information for a product by utilizing customer-provided details such as country, quantity, and options, along with product reference. Returns detailed pricing information to the assistant agent for customer communication.",
)

the_human = ConversableAgent(
    name="the_human",
    human_input_mode="ALWAYS",
)

def custom_speaker_selection_func(last_speaker: Agent, groupchat: GroupChat):
    """Custom function to determine the next speaker in a structured agent workflow."""
    messages = groupchat.messages

    # if len(messages) <= 1:
    #     return the_human  # Start with the human agent

    if last_speaker is the_human:
        return assistant

    elif last_speaker is assistant:
        if messages and messages[-1].get("role") == "assistant" and messages[-1].get("tool_calls"):
            return executor_agent
        else:
            return the_human 

    elif last_speaker is executor_agent:
        return assistant

    else:
        return "random"

planning_chat = GroupChat(
    agents=[the_human, assistant, executor_agent],
    messages=[],
    max_round=40,
    speaker_selection_method=custom_speaker_selection_func,
)

planning_manager = GroupChatManager(
    groupchat=planning_chat,
)

chat_initialized = False # pylint: disable=C0103


@app.route("/")
def index():
    """Renders the index.html template."""
    return render_template("index.html")


@socket_io.on("user_message")
def handle_user_message(data):
    """Handles user messages received via Socket.IO."""
    global chat_initialized

    user_message = data.get("message")

    if not user_message:
        emit("message", {"sender": "system", "content": "Error: No message provided."})
        return

    if not chat_initialized:
        chat_initialized = True
        the_human.initiate_chat(
            recipient=planning_manager,
            message=user_message,
        )
    else:
        the_human.send(
            recipient=planning_manager,
            message=user_message,
        )

if __name__ == "__main__":
    socket_io.run(app, debug=True, use_reloader=False)
