import httpx
import time
from linebot import LineBotApi
import uuid

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
from src.chat import BaseChatApp

class LineApp(BaseChatApp):
    def __init__(
            self, 
            access_token: str=LINE_CHANNEL_ACCESS_TOKEN, 
            channel_secret: str=LINE_CHANNEL_SECRET):
        self.channel_access_token = access_token
        self.channel_secret = channel_secret
        self.line_bot_api = LineBotApi(self.channel_access_token)
        self.configuration = Configuration(access_token=self.channel_access_token)

    async def send_follow_up_message(
        self,
        to: str,
        messages: str,
        retry_key: str | None = None
    ):
        """
        Send push messages via LINE Bot API using httpx
    
        Args:
            channel_access_token (str): LINE channel access token
            to (str): User ID, group ID, or room ID
            messages (List[Dict]): List of message objects
            retry_key (str, optional): UUID for retry key. Auto-generated if not provided.
        
        Returns:
            dict: JSON response from LINE API
        """
        url = "https://api.line.me/v2/bot/message/push"
    
        # Generate UUID for retry key if not provided
        if retry_key is None:
            retry_key = str(uuid.uuid4())
    
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
            "X-Line-Retry-Key": retry_key
        }
    
        payload = {
            "to": to,
            "messages": [{"type": "text", "text": messages}]
        }
    
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
        
            # Print detailed response info (equivalent to curl -v)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text}")
        
            response.raise_for_status()
        
            # LINE API returns empty response body on success
            if response.text:
                return response.json()
            else:
                return {"status": "success", "message": "Push message sent"}

    def get_bot_response(self, messages, api_client: ApiClient = None, reply_token: str = None):
        operator_agent = get_operator_agent()
        line_bot_api = MessagingApi(api_client)        
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


    def save_to_gsheet(
            self, 
            user_id: str, 
            display_name: str
            ):
        client_tag_sheet = ClientTagSheet()
        if not client_tag_sheet.has_profle(display_name):
            client_tag_sheet.add_new_profile(
                profile_name=display_name,
                user_id=user_id,
                platform=Platform.LINE
            )

        else:
            client_tag_sheet.update_timestamp(
                profile_name=display_name
            )

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

            messages_history = chat_history.get_chat_history(user_id)
            messages = messages_history + [Message(role="user", content=message)]

            self.get_bot_response(
                messages=messages,
                api_client=api_client,
                reply_token=reply_token
            )

            self.save_to_gsheet(
                user_id=user_id,
                display_name=user_profile.display_name
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

if __name__ == "__main__":
    import asyncio
    # Example usage
    line_app = LineApp()
    user_id = "U641ab55606860da3924cd1044c04b8f7"  # Replace with actual user ID
    message = "Hello, this is a test message."

    # send follow-up message
    messages = [{"type": "text", "text": message}]
    response = asyncio.run(line_app.send_follow_up_message(
            to=user_id,
            messages=messages
        )
    )


    print("Response from LINE API:", response)
