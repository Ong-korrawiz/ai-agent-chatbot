import httpx
import time
from linebot import LineBotApi

from src.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from src.gcp.sql import ChatHistoryTable, UserTable, CloudSqlManager
from src.gcp.gsheet import ClientTagSheet
from src.agents.customer_service import get_operator_agent
from src._types import Message, Platform
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
    def __init__(
            self, 
            access_token: str=LINE_CHANNEL_ACCESS_TOKEN, 
            channel_secret: str=LINE_CHANNEL_SECRET):
        self.channel_access_token = access_token
        self.channel_secret = channel_secret
        self.line_bot_api = LineBotApi(self.channel_access_token)
        self.configuration = Configuration(access_token=self.channel_access_token)

    async def send_follow_up_message(self, user_id: str, message: str):
        # Logic to send a message using LINE Messaging API
        self.send_message(user_id, message)

    def reply_message(self, user_id: str, message: str, reply_token: str):
        """
        Sends a reply message to the user.
        
        Args:
            user_id (str): The LINE user ID.
            message (str): The message to send.
            reply_token (str): The token to reply to the user.
        """
        timestamp = str(int(time.time()))
        user_profile = self.line_bot_api.get_profile(user_id)
 
        chat_history = ChatHistoryTable()
        user_table = UserTable()

        with ApiClient(self.configuration) as api_client:

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

            client_tag_sheet = ClientTagSheet()
            if not client_tag_sheet.has_profle(user_profile.display_name):
                client_tag_sheet.add_new_profile(
                    profile_name=user_profile.display_name,
                    user_id=user_id,
                    platform=Platform.LINE
                )


            else:
                client_tag_sheet.update_timestamp(
                    profile_name=user_profile.display_name
                )

            user_table.insert(
                user_uuid=user_id,
                name=user_profile,
                metadata="{}"
            )

            chat_history.insert(
                user_uuid=user_id,
                role="user",
                content=message,
                messenger_timestamp=timestamp
            )

            chat_history.insert(
                user_uuid=user_id,
                role="assistant",
                content=response,
                messenger_timestamp=timestamp
            )
