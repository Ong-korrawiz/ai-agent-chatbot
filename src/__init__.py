import httpx
import time
from linebot import LineBotApi

from src.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from src.gcp.sql import ChatHistoryTable, UserTable, CloudSqlManager
from src.agents.customer_service import get_operator_agent
from src._types import Message
from linebot.v3.messaging import (
    ApiClient, 
    MessagingApi, 
    Configuration, 
    ReplyMessageRequest, 
    TextMessage, 
    # FlexMessage, 
    # Emoji,
)
from src.agents.functions import add_contact_info


class LineApp:
    def __init__(self, channel_access_token: str, channel_secret: str):
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret
        self.line_bot_api = LineBotApi(channel_access_token)

    async def send_message(self, user_id: str, message: str):
        # Logic to send a message using LINE Messaging API
        pass

    def reply_message(self, user_id: str, message: str, reply_token: str):
        """
        Sends a reply message to the user.
        
        Args:
            user_id (str): The LINE user ID.
            message (str): The message to send.
        """
        timestamp = str(int(time.time()))
        user_profile = self.line_bot_api.get_profile(user_id)

        chat_history = ChatHistoryTable()
        user_table = UserTable()

        configuration = Configuration(access_token=self.channel_access_token)


        with ApiClient(configuration) as api_client:

            operator_agent = get_operator_agent()
            line_bot_api = MessagingApi(api_client)        
            messages_history = chat_history.get_chat_history(user_id)
            messages = messages_history + [Message(role="user", content=message)]
            response = operator_agent.invoke_with_function_calling(
                messages,
                functions=add_contact_info
            )

            reply_message = TextMessage(text=response)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[reply_message]
                )
            )

            user_table.insert(
                user_uuid=user_id,
                name=user_profile,
                metadata="{}"
            )
            chat_history.insert(
                user_uuid=user_id,
                role="user",
                content=message["text"],
                messenger_timestamp=timestamp
            )
            chat_history.insert(
                user_uuid=user_id,
                role="assistant",
                content=response,
                messenger_timestamp=timestamp
            )


    # def get_user_profile(self, user_id: str):
    #     """
    #     Fetches the user profile from LINE using the user ID.
        
    #     Args:
    #         user_id (str): The LINE user ID.
        
    #     Returns:
    #         dict: User profile information.
    #     """
    #     headers = {
    #         'Authorization': f'Bearer {self.channel_access_token}'
    #     }
    #     response = httpx.get(f'https://api.line.me/v2/bot/profile/{user_id}', headers=headers)
    #     return response.json() if response.status_code == 200 else Noneimport timeimport time