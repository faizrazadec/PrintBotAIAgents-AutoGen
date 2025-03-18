from langchain.chat_models import init_chat_model
import getpass
import os
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_redis import RedisChatMessageHistory
import logging
from langchain_core.output_parsers import StrOutputParser
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

def get_redis_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieves chat history from Redis."""
    return RedisChatMessageHistory(session_id, redis_url=REDIS_URL)

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
    get_redis_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Continuous conversation loop
session_id = "mugees1"
logger.info("Chat session started. Type 'exit' to end.")

while True:
    user_input = input("User: ")  # Get user input
    if user_input.lower() in ["exit", "quit"]:
        logger.info("User ended the chat.")
        print("AI: Goodbye! 👋")
        break

    result = chain_with_history.invoke(
        {"input": user_input}, config={"configurable": {"session_id": session_id}}
    )
    
    print(f"AI: {result}")
