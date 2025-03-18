from langchain.chat_models import init_chat_model
import getpass
import os
import json
import logging
import requests
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_redis import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import initialize_agent, Tool
from src.system_messages import message_1

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure API key is set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

# Connect to Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
logger.info("Connecting to Redis at: %s", REDIS_URL)

# API Endpoints
URL_PRODUCTS = "https://api.cloudprinter.com/cloudcore/1.0/products"
URL_PRODUCT_INFO = "https://api.cloudprinter.com/cloudcore/1.0/products/info"

# API Key
API_KEY = "bed884d6def704a005fa85b2605dac91"

# Fetch product data
headers = {'Content-Type': 'application/json'}
payload = json.dumps({"apikey": API_KEY})

response = requests.post(URL_PRODUCTS, headers=headers, data=payload)
PRODUCTS = json.loads(response.text)

# Function to filter products by category
def filter_products_by_category(category_name: str):
    """Fetches products based on the given category name."""
    filtered_products = [
        product for product in PRODUCTS if product["category"].lower() == category_name.lower()
    ]
    
    if not filtered_products:
        return {"error": "No products found for the given category."}

    return filtered_products  # Returns list of matching products

# Function to get product info by reference
def get_product_info_by_reference(reference: str):
    """Fetches detailed information about a product using its reference."""
    payload = json.dumps({
        "apikey": API_KEY,
        "reference": reference
    })
    
    response = requests.post(URL_PRODUCT_INFO, headers=headers, data=payload)
    
    return response.json()  # Return product details

# Convert functions into LangChain tools
filter_products_tool = Tool(
    name="FilterProductsByCategory",
    func=filter_products_by_category,
    description="Retrieves products based on the user's specified category. Then, prompts the user to specify product details based on the provided notes. Once the user selects a product, its reference is used to fetch detailed information through another tool. Ask Everything from the user, don't choose anything by your own. When you choose the category, search it by making it singular."
)

get_product_info_tool = Tool(
    name="GetProductInfoByReference",
    func=get_product_info_by_reference,
    description="Gets detailed information about a product using its reference from the api hit so the input of this tool will be only the refrence"
)

# Initialize model
model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai"
)

# Define prompt structure
prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(message_1),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}"),
    ]
)

# Create the chain
chain = prompt | model | StrOutputParser()
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: RedisChatMessageHistory(session_id, redis_url=REDIS_URL),
    input_messages_key="input",
    history_messages_key="history",
)

# Initialize an agent with both tools
agent = initialize_agent(
    tools=[filter_products_tool, get_product_info_tool],  # Register both tools
    llm=model,
    agent="zero-shot-react-description",  # This lets the model decide when to call tools
    verbose=True
)

# Continuous conversation loop
session_id = "mugees2"
logger.info("Chat session started. Type 'exit' to end.")

while True:
    user_input = input("User: ")  # Get user input
    if user_input.lower() in ["exit", "quit"]:
        logger.info("User ended the chat.")
        print("AI: Goodbye! 👋")
        break

    # First, let the agent try to respond and use tools if needed
    result = agent.run(user_input)

    print(f"AI: {result}")
