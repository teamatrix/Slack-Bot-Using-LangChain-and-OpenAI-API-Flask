import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify
from functions import draft_email

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment variables
required_env_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "SLACK_BOT_USER_ID"]
for var in required_env_vars:
    if var not in os.environ:
        logger.error(f"Missing required environment variable: {var}")
        exit(1)

# Set Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize the Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

def get_bot_user_id():
    """
    Get the bot user ID using the Slack API.
    Returns:
        str: The bot user ID.
    """
    try:
        # Initialize the Slack client with your bot token
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        response = slack_client.auth_test()
        return response["user_id"]
    except SlackApiError as e:
        logger.error(f"Slack API Error: {e.response['error']}")
        return None

def my_function(text):
    """
    Custom function to process the text and return a response.
    In this example, the function converts the input text to uppercase.

    Args:
        text (str): The input text to process.

    Returns:
        str: The processed text.
    """
    return text.upper()

@app.event("app_mention")
def handle_mentions(body, say):
    """
    Event listener for mentions in Slack.
    When the bot is mentioned, this function processes the text and sends a response.

    Args:
        body (dict): The event data received from Slack.
        say (callable): A function for sending a response to the channel.
    """
    text = body["event"]["text"]

    mention = f"<@{SLACK_BOT_USER_ID}>"
    text = text.replace(mention, "").strip()

    say("Sure, I'll get right on that!")
    response = draft_email(text)
    say(response)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Route for handling Slack events.
    This function passes the incoming HTTP request to the SlackRequestHandler for processing.

    Returns:
        Response: The result of handling the request.
    """
    try:
        return handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Run the Flask app
if __name__ == "__main__":
    bot_user_id = get_bot_user_id()
    if bot_user_id:
        logger.info(f"Bot User ID: {bot_user_id}")
    else:
        logger.error("Failed to get Bot User ID.")
        exit(1)

    # Run the Flask app
    flask_app.run(host='0.0.0.0', port=5000)
