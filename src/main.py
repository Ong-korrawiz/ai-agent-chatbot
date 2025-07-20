import os
import uvicorn
import time

from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Header, Response, BackgroundTasks

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from linebot.v3.messaging import (
    ApiClient, 
    MessagingApi, 
    Configuration, 
    ReplyMessageRequest, 
    TextMessage, 
    # FlexMessage, 
    # Emoji,
)
from linebot.v3.messaging import TextMessage, Emoji
import logging
from pprint import pprint

from src._types import Message, MessengerWebhookData
from src.agents.customer_service import get_operator_agent
from src.chat.messenger import Messenger
from src.chat.line import LineApp
from src.gcp.sql import ChatHistoryTable, UserTable ,CloudSqlManager
from src.gcp.gsheet import ClientTagSheet
from src.agents.functions import add_contact_info
# from src.db import ChatHistory, User
from src.settings import MESSENGER_VERIFY_TOKEN

logger = logging.getLogger(__name__)

app = FastAPI()

load_dotenv(override=True)


get_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN').replace('"', '')
get_channel_secret = os.getenv('LINE_CHANNEL_SECRET').replace('"', '')

configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)

class MessageHistory:
    history = []

MESSAGE_HISTORY = MessageHistory()


@app.post("/callback")
async def callback(request: Request):
    x_line_signature = request.headers['X-Line-Signature']
    print("Received request with X-Line-Signature:", x_line_signature)
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError as e:
        print(f"Invalid signature error: {str(e)}")
        # Log the error for debugging
        logger.error(f"Invalid signature error: {str(e)}")
        print(f"Channel Access Token: {get_access_token}")
        print(f"Channel Secret: {get_channel_secret}")
        print(f"Request Body: {body_str}")
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'


@app.get("/messenger_callback")
def init_messenger(request: Request):
	# FB sends the verify token as hub.verify_token
    fb_token = request.query_params.get("hub.verify_token")

    # we verify if the token sent matches our verify token
    if fb_token == MESSENGER_VERIFY_TOKEN:
    	# respond with hub.challenge parameter from the request.
        return Response(content=request.query_params["hub.challenge"])
    return 'Failed to verify token'



def get_message_timestamp(data: MessengerWebhookData) -> str:
    if not data.object == "page":
        return None
    for entry in data.entry:
        messaging_events = [
            event for event in entry.get("messaging", []) if event.get("message")
        ]
        if messaging_events:
            return messaging_events[0]["timestamp"]
    return None
    



@app.post("/messenger_callback", status_code=200)
async def webhook(data: MessengerWebhookData, background_tasks: BackgroundTasks):
    """
    Messages handler.
    """
    print("Get webhook data")
    start_time = time.time()
    print(f"Start time: {start_time}")
    async def send_message_task(data: MessengerWebhookData):
        """
        Background task to send message to Messenger.
        """
        print("Processing Messenger webhook data...") 
        messenger = Messenger(
            page_access_token=MESSENGER_VERIFY_TOKEN
        )
        await messenger.send_message_to_messenger(data)

    background_tasks.add_task(send_message_task, data)
    processing_time = time.time() - start_time
    print(f"Processing time: {processing_time} seconds")
    
    return Response(
        status_code=200,
        content="OK"
    )



@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):

    if not event.message.text:
        print("Received an empty message.")
        return None

    line_app = LineApp(
        access_token=get_access_token,
        channel_secret=get_channel_secret
    )
    user_id = event.source.user_id
    reply_token = event.reply_token
    message = event.message.text
    print(f"Received message from user {user_id}: {message}")
    line_app.reply_message(
        user_id=user_id,
        message=message,
        reply_token=reply_token
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)