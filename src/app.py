"""This module implements a Flask application with AutoGen and Socket.IO for real-time chat."""

import os
import json
from urllib.parse import urlencode
import requests
from typing import Union, Any
import uuid
from werkzeug.utils import secure_filename

from flask import (
    Flask, 
    render_template,
    request,
    jsonify,
    render_template_string
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
    fetch_pricing_info,
    create_order,
    set_uploaded_file_path
)
from logger import setup_logger

load_dotenv()
logger = setup_logger()
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session
socket_io = SocketIO(app, cors_allowed_origins="*")

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# OAuth Configuration
CLIENT_ID = "сhatbot_testing"
CLIENT_SECRET = "c39e7fafcbbede1d85bb695ab628aa61" 
REDIRECT_URI = "http://127.0.0.1:5000"  # No /callback path
STATE = "1"  # In production, use a random string for security
SCOPE = "read-write"  # Or "read" depending on your needs
RESPONSE_TYPE = "code"

# Authorization URL
auth_url = "https://api.cloudprinter.com/cloudauth/1.0/oauth2/authorize"
token_url = "https://api.cloudprinter.com/cloudauth/1.0/oauth2/token"

# Global variable to store token data
token_data = None

# HTML template for auth popup
AUTH_POPUP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cloudprinter.com Authorization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
        }
        .loader {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h2>Redirecting to Cloudprinter.com</h2>
    <p>Please wait while we redirect you to the authorization page...</p>
    <div class="loader"></div>
    
    <script>
        // Redirect to the authorization URL
        window.location.href = "{{ auth_url|safe }}";
    </script>
</body>
</html>
"""

# HTML template for oauth return page
OAUTH_RETURN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Complete</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
        }
        .success {
            color: #4CAF50;
            font-size: 24px;
        }
    </style>
</head>
<body>
    <h2 class="success">Authorization Successful!</h2>
    <p>You can close this window now. Returning to the main application...
    
    <script>
        // Close this window after a brief delay
        setTimeout(function() {
            window.close();
        }, 2000);
    </script>
</body>
</html>
"""

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
    
    # Flag authentication-related messages
    login_trigger = False
    auth_keywords = ['login', 'log in', 'not logged in', 'authentication required', 'need to authenticate']
    
    if sender.name != "the_human" and message_content:
        for keyword in auth_keywords:
            if keyword.lower() in message_content.lower():
                login_trigger = True
                break
    
    socket_io.emit("message", {
        "sender": sender.name, 
        "content": message_content,
        "login_required": login_trigger
    })

GroupChatManager._print_received_message = new_print_received_message

llm_config = {
    "config_list": [
        {
            "api_type": "openai",
            "model": "gpt-4o",
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
    functions=[filter_products_by_category, get_product_info_by_reference, fetch_pricing_info, create_order],
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

register_function(
    create_order,
    caller=assistant,
    executor=executor_agent,
    description="Submits a print order to the Cloudprinter API using the provided customer email, address, and item details. Returns the API response for order creation.",
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
    # max_round=40,
    speaker_selection_method=custom_speaker_selection_func,
)

planning_manager = GroupChatManager(
    groupchat=planning_chat,
)

chat_initialized = False


@app.route("/")
def index():
    """Renders the index.html template."""
    # Check if this is a callback from OAuth provider
    code = request.args.get('code')
    state = request.args.get('state')
    
    if code and state:
        # This is a callback from OAuth
        return handle_oauth_callback(code, state)
    else:
        # This is a normal visit to the index page
        return render_template("index.html")
    
    
def handle_oauth_callback(code, state):
    """Process the OAuth callback parameters"""
    global token_data
    
    if state != STATE:
        return "State mismatch. Possible CSRF attack."
    
    # Exchange the authorization code for an access token
    token_payload = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    token_response = requests.post(token_url, data=token_payload, headers=headers)
    logger.info(f"Token response: {token_response.text}")
    
    if token_response.status_code == 200:
        # Store the token data
        token_data = token_response.json()
        
        # Store token in the token manager for API calls
        from functions import token_manager
        token_manager.set_token(token_data.get('access_token'))
        logger.info("Token successfully stored in token manager")
        
        # Store token info in a file (optional)
        with open('cloudprinter_token.json', 'w') as f:
            json.dump(token_data, f)
            
        return render_template_string(OAUTH_RETURN_TEMPLATE)
    else:
        return f"Error exchanging code for token: {token_response.text}"
    
    
@app.route('/auth')
def auth():
    """Display the auth popup that redirects to Cloudprinter"""
    # Prepare the authorization URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": STATE,
        "scope": SCOPE,
        "response_type": RESPONSE_TYPE,
    }
    authorization_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"Authorization URL: {authorization_url}")
    
    return render_template_string(AUTH_POPUP_TEMPLATE, auth_url=authorization_url)


@app.route('/check_token')
def check_token():
    """Endpoint for the main page to check if authentication is complete"""
    global token_data
    
    if token_data:
        return jsonify({
            "authenticated": True,
            "access_token": token_data.get('access_token'),
            "refresh_token": token_data.get('refresh_token', None),
            "expires_in": token_data.get('expires_in', None)
        })
    else:
        return jsonify({"authenticated": False})


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        set_uploaded_file_path(file_path)
        return jsonify({"message": "File successfully uploaded", "file_path": file_path}), 201
    else:
        return jsonify({"error": "Allowed file types are pdf"}), 400


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
