```markdown
# PrintBotAIAgents-AutoGen

This project demonstrates a real-time chat application using Flask, Socket.IO, and AutoGen to create an AI-powered product assistant. The assistant helps users find and configure print products by interacting with a remote API.

## Features

-   **Real-time Chat:** Utilizes Flask-SocketIO for bidirectional, event-based communication.
-   **AutoGen Integration:** Employs AutoGen agents for intelligent product selection and configuration.
-   **API Interaction:** Fetches product data from a remote API.
-   **Product Filtering:** Allows users to filter products by category and refine their selections based on product notes and specifications.
-   **Step-by-Step Guidance:** Guides users through the product selection process with one-by-one information gathering.
-   **Customizable Prompts:** Uses customizable prompts to control the behavior of the AI assistant and manager agents.
-   **Robust Error Handling:** Includes error handling for API requests and Socket.IO events.

## Prerequisites

-   Python 3.7+
-   pip
-   An OpenAI API key
-   A Cloudprinter API key

## Installation

1.  **Clone the repository:**

    ```bash
    git clone [repository_url]
    cd PrintBotAIAgents-AutoGen/src
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    .venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    -   Create a `.env` file in the project's root directory.
    -   Add your OpenAI and Cloudprinter API keys:

        ```
        OPENAI_API_KEY=your_openai_api_key
        CLOUDPRINTER_API_KEY=your_cloudprinter_api_key
        ```

## Running the Application

1.  **Start the Flask application:**

    ```bash
    python app.py
    ```

2.  **Open `index.html` in your browser:**

    -   Navigate to `http://127.0.0.1:5000/` in your web browser.

## Project Structure

```
PrintBotAIAgents-AutoGen/
├── src/
│   ├── app.py             # Flask application with AutoGen and Socket.IO
│   ├── functions.py       # Functions for interacting with the Cloudprinter API.
│   ├── prompts.py         # Prompts for AutoGen agents.
│   ├── logger.py          # Logger setup.
│   ├── templates/
│   │   └── index.html     # HTML template for the chat interface.
│   ├── .env               # Environment variables.
│   └── requirements.txt   # Project dependencies.
└── README.md
```

## Usage

-   Open the web application in your browser.
-   Type your product requests into the chat interface.
-   Follow the assistant's prompts to select and configure your desired product.

## Customization

-   **Modify Prompts:** Change the prompts in `prompts.py` to customize the behavior of the AI agents.
-   **Extend Functions:** Add more functions to `functions.py` to interact with additional APIs or data sources.
-   **UI Customization:** Modify `index.html` and add CSS to improve the user interface.
-   **Add More Agents:** Add more autogen agents to perform different tasks.

## Dependencies

-   Flask
-   Flask-SocketIO
-   AutoGen
-   Requests
-   python-dotenv

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the [MIT License](LICENSE).
```
