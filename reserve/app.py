from flask import Flask, request, jsonify, render_template
import os
import autogen
from autogen import (
    ConversableAgent,
    register_function,
    GroupChatManager,
    GroupChat,
)
from prompts import assistant_prompt
from dotenv import load_dotenv

load_dotenv()

from functions import (
    filter_products_by_category,
    get_product_info_by_reference,
)

from logger import setup_logger

logger = setup_logger()

from flask_socketio import SocketIO, emit
from typing import Union, Any

# Initialize Flask app
app = Flask(__name__)
socket_io = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for Socket.IO

# Patch the GroupChatManager to emit messages via Socket.IO
# def new_print_received_message(self, message: Union[dict[str, Any], str], sender):
#     message = self._message_to_dict(message)
#     message_content = message.get("content", "")
#     print(f"PATCHED: Sender={sender.name}, Content={message_content}")
#     socket_io.emit('message', {"sender": sender.name, "content": message_content})

def new_print_received_message(self, message: Union[dict[str, Any], str], sender):
    message = self._message_to_dict(message)
    message_content = message.get("content", "")

    # Filter conditions
    if (sender.name == "assistant_agent" and not message_content) or sender.name == "executor_agent":
        print(f"Filtered out: Sender={sender.name}, Content={message_content}")
        return  # Skip emitting this message

    # Log and emit the message
    print(f"PATCHED: Sender={sender.name}, Content={message_content}")
    socket_io.emit('message', {"sender": sender.name, "content": message_content})

GroupChatManager._print_received_message = new_print_received_message

# Autogen configuration
llm_config_turbo = {
    "config_list": [
        {
            "api_type": "openai",
            "model": "gpt-4-turbo",
            "api_key": os.environ["OPENAI_API_KEY"],
        }
    ],
}

llm_config = {
    "config_list": [
        {
            "api_type": "openai",
            "model": "gpt-4o-mini",
            "api_key": os.environ["OPENAI_API_KEY"],
        }
    ],
}

# Initialize Autogen agents
executor_agent = ConversableAgent(
    name="executor_agent",
    human_input_mode="NEVER",
    system_message="You are the executor agent. Your role is to execute function calls and provide the results to the assistant agent.",
)

assistant = ConversableAgent(
    name="assistant_agent",
    llm_config=llm_config,
    system_message=assistant_prompt,
    human_input_mode="NEVER",
    functions=[filter_products_by_category, get_product_info_by_reference],
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

the_human = ConversableAgent(
    name="the_human",
    human_input_mode="ALWAYS",
)

planning_chat = GroupChat(
    agents=[the_human, assistant, executor_agent],
    messages=[],
    max_round=40,
    send_introductions=True,
    speaker_selection_method="auto",
)

planning_manager = GroupChatManager(
    groupchat=planning_chat,
    llm_config=llm_config_turbo,
    system_message="You are the manager. The *human agent* provides input to the *assistant agent*. The *assistant agent* can call tools, which are executed by the *executor agent*. The output from the *executor agent* is then passed back to the *assistant agent*, allowing it to process the results and request further input from the *human agent* as needed.",
)

chat_initialized = False

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

# Socket.IO event for handling user messages
@socket_io.on('user_message')
# def handle_user_message(data):
#     user_message = data.get('message')

#     if not user_message:
#         emit('message', {"sender": "system", "content": "Error: No message provided."})
#         return

#     # Pass the user's message to the Autogen group chat
#     the_human.initiate_chat(
#         recipient=planning_manager,
#         message=user_message,

#     )
@socket_io.on('user_message')
def handle_user_message(data):
    global chat_initialized

    user_message = data.get('message')

    if not user_message:
        emit('message', {"sender": "system", "content": "Error: No message provided."})
        return

    # Initialize the chat only once
    if not chat_initialized:
        chat_initialized = True
        the_human.initiate_chat(
            recipient=planning_manager,
            message=user_message,
        )
    else:
        # Continue the existing conversation
        the_human.send(
            recipient=planning_manager,
            message=user_message,
        )


# Run the Flask app with Socket.IO
if __name__ == '__main__':
    socket_io.run(app, debug=True)

# design_chat_result = planning_manager.initiate_chat(
#     recipient=the_human,
#     message="Hi there, What prducts you're looking for?"
# )
    
# print(design_chat_result.chat_history)