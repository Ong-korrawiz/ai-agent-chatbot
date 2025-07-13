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

from src._types import Message, MessengerWebhookRequestData
from src.agents.customer_service import get_operator_agent
from src.utils.messenger import Messenger
from src.gcp.sql import ChatHistoryTable, UserTable ,CloudSqlManager 
# from src.db import ChatHistory, User

logger = logging.getLogger(__name__)

app = FastAPI()

load_dotenv(override=True)


get_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN').replace('"', '')
get_channel_secret = os.getenv('LINE_CHANNEL_SECRET').replace('"', '')
messenger_verify_token = os.getenv('MESSENGER_WEBHOOK_TOKEN').replace('"', '')

configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)

class MessageHistory:
    history = []

MESSAGE_HISTORY = MessageHistory()


@app.post("/callback")
async def callback(request: Request):
    x_line_signature = request.headers['X-Line-Signature']
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError as e:
        print(f"Invalid signature error: {str(e)}")
        # Log the error for debugging
        logger.error(f"Invalid signature error: {str(e)}")
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'


@app.get("/messenger_callback")
def init_messenger(request: Request):
	# FB sends the verify token as hub.verify_token
    fb_token = request.query_params.get("hub.verify_token")

    # we verify if the token sent matches our verify token
    if fb_token == messenger_verify_token:
    	# respond with hub.challenge parameter from the request.
        return Response(content=request.query_params["hub.challenge"])
    return 'Failed to verify token'


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     response = await call_next(request)
#     print("Processing request...")
#     return Response(
#         status_code=200,
#         content="OK",
#     )

def get_message_timestamp(data: MessengerWebhookRequestData) -> str:
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
async def webhook(data: MessengerWebhookRequestData, background_tasks: BackgroundTasks):
    """
    Messages handler.
    """
    start_time = time.time()
    print(f"Start time: {start_time}")



    async def send_message_to_messenger(data: MessengerWebhookRequestData):
        print("Processing Messenger webhook data ...", data)
        timestamp = data.get_message_timestamp
        sender_id = data.get_sender_id

        print(f"Check tabes in database ...")
        manager = CloudSqlManager()
        engine = manager.get_engine()

        # Create tables if they do not exist
        chat_history = ChatHistoryTable(engine=engine)
        user_table = UserTable(engine=engine)
        manager.create_table()
    
        print(f"Check if user {sender_id} exists in database ...")
        messages = chat_history.get_chat_history(sender_id)
        
        if messages:
            last_message = messages[-1]
            print(f"Last message timestamp: {last_message.messenger_timestamp}, Current timestamp: {timestamp}")

            if str(last_message.messenger_timestamp).strip() == str(timestamp).strip():
                print("No new messages to process.")
                return Response(status_code=200, content="No new messages to process.")


        if not data.object == "page":
            return Response(status_code=200, content="Data object is not 'page'")
        
        operator_agent = get_operator_agent()
    
        for entry in data.entry:
            messaging_events = [
                event for event in entry.get("messaging", []) if event.get("message")
            ]

            for event in messaging_events:
                message = event.get("message")
                sender_id = event["sender"]["id"]

                messenger = Messenger(
                    page_access_token=messenger_verify_token
                )

                if not messages:
                    messages = []
                messages.append(Message(role="user", content=message["text"]))

                response = operator_agent.invoke(
                    # [Message(role="user", content=message["text"])]
                    messages
                    )
                await messenger.send_message(
                                recipient_id=sender_id,
                                message_text=response
                                )
                
                
                
                user_table.insert(
                    user_uuid=sender_id,
                    name=sender_id,  # Assuming a mock name for now
                    metadata="{}"
                )
                chat_history.insert(
                    user_uuid=sender_id,
                    role="user",
                    content=message["text"],
                    messenger_timestamp=timestamp
                )
                chat_history.insert(
                    user_uuid=sender_id,
                    role="assistant",
                    content=response,
                    messenger_timestamp=timestamp
                )
                print(f"Sent message to {sender_id}: {response}")

    background_tasks.add_task(send_message_to_messenger, data)
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
    manager = CloudSqlManager()
    manager.create_table()
    engine = manager.get_engine()

    chat_history = ChatHistoryTable(engine=engine)
    user_table = UserTable(engine=engine)

    with ApiClient(configuration) as api_client:

        operator_agent = get_operator_agent()
        line_bot_api = MessagingApi(api_client)
        


        logger.info("Done inserting user message into chat history")
        
        messages_history = chat_history.get_chat_history(event.source.user_id)
        messages = messages_history + [Message(role="user", content=event.message.text)]
        response = operator_agent.invoke(
            messages
        )

        reply_message = TextMessage(text=response)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )

        user_table.insert(
            user_uuid=event.source.user_id,
            name=event.source.user_id,  # Assuming user_id is used as name
            metadata="{}"  # Assuming metadata is empty for now
        )

        chat_history.insert(
            user_uuid=event.source.user_id,
            role="user",
            content=event.message.text
        )
        chat_history.insert(
            user_uuid=event.source.user_id,
            role="assistant",
            content=response
        )

        logger.info("Done inserting bot message into chat history")

        if not reply_message:
            return None



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)