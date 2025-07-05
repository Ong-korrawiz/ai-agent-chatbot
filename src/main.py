import os
import uvicorn

from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Header

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
from logging import getLogger
from pprint import pprint

from src._types import Message
from src.agents.customer_service import get_operator_agent
# from src.db import ChatHistory, User

logger = getLogger(__name__)

app = FastAPI()

load_dotenv(override=True)

# # LINE Access Key
# get_access_token = os.getenv('ACCESS_TOKEN')
# # LINE Secret Key
# get_channel_secret = os.getenv('CHANNEL_SECRET')

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
    body = await request.body()
    body_str = body.decode('utf-8')
    
    print(f"Request body: {body_str}")

    # print channel secret and access token for debugging
    print(f"Channel Secret: {get_channel_secret}")
    print(f"Access Token: {get_access_token}")

    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError as e:
        print(f"Invalid signature error: {str(e)}")
        # Log the error for debugging
        logger.error(f"Invalid signature error: {str(e)}")
        pprint({
            "error": "Invalid signature",
            "x_line_signature": x_line_signature,
            "body": body_str,
            "channel_secret": get_channel_secret,
            "access_token": get_access_token
        })
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):



    if not event.message.text:
        print("Received an empty message.")
        return None

    with ApiClient(configuration) as api_client:

        operator_agent = get_operator_agent()
        line_bot_api = MessagingApi(api_client)
        
        MESSAGE_HISTORY.history.append(
            Message(role="user", content=event.message.text)
        )
        # user_db = User()
        # if not user_db.has_user(event.source.user_id):
        #     logger.info(f"User {event.source.user_id} does not exist, inserting into database")
        #     user_db.insert(
        #         uuid=event.source.user_id,
        #         name="",
        #         metadata=""
        #     )

        # user_chat = ChatHistory().insert(
        #     user_uuid=event.source.user_id,
        #     role="user",
        #     content=event.message.text
        # )
        logger.info("Done inserting user message into chat history")
        
        response = operator_agent.invoke(
            [Message(role="user", content=event.message.text)]
        )

        reply_message = TextMessage(text=response + "peko")

        MESSAGE_HISTORY.history.append(
            Message(role="assistant", content=response)
        )

        # bot_chat = ChatHistory().insert(
        #     user_uuid=event.source.user_id,
        #     role="assistant",
        #     content=response
        # )

        logger.info("Done inserting bot message into chat history")



        if not reply_message:
            return None

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)