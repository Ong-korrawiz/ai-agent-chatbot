from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from typing import List
import uvicorn
import httpx
import os
from src._types import Message, MessengerWebhookData, Platform
from src.gcp.sql import ChatHistoryTable, UserTable
from src.agents.customer_service import get_operator_agent
from src.settings import MESSENGER_VERIFY_TOKEN
from src.gcp.gsheet import ClientTagSheet, ConfigSheet
from src.agents.functions import add_contact_info
from src.chat import BaseChatApp


class Messenger(BaseChatApp):
# Helpers.
    def __init__(self, page_access_token: str = None, messenger_verify_token: str = MESSENGER_VERIFY_TOKEN):
        if not page_access_token:
            self.page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").replace('"', '')

        else:
            self.page_access_token = page_access_token
        self.messenger_verify_token = messenger_verify_token

    async def send_message(
        self,
        recipient_id: str,
        message_text: str,
        message_type: str = "UPDATE",
    ):
        """
        Send message to specific user(By recipient ID) from specific page(By
        access token).

        Arguments:
            page_access_token: (string) Target page access token.
            recipient_id: (string) The ID of the user that the message is
            addressed to.
            message_text: (string) The content of the message.
            message_type: (string) The type of the target message.
            RESPONSE, UPDATE or MESSAGE_TAG - the accurate description -
            https://developers.facebook.com/docs/messenger-platform/send-messages/#messaging_types
        """
        page_access_token = self.page_access_token

        response = httpx.post(
            "https://graph.facebook.com/v23.0/me/messages",
            params={"access_token": page_access_token},
            headers={
                "Content-Type": "application/json"
                
                },
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
                "messaging_type": message_type,
            },
        )
        response.raise_for_status()


    def get_user_profile(self, user_id: str):
        """
        Get user profile information by user ID.
        """
        response = httpx.get(
            f"https://graph.facebook.com/v2.6/{user_id}",
            params={"access_token": self.page_access_token, "fields": "name, picture"},
        )
        response.raise_for_status()
        return response.json()


    def get_user_info_messenger(self, psid):
        url = f"https://graph.facebook.com/{psid}"
        params = {
            "fields": "first_name,last_name,profile_pic",
            "access_token": self.page_access_token
        }
    
        with httpx.Client() as client:
            response = client.get(url, params=params)
            response.raise_for_status()  # Raises an exception for bad status codes
            return response.json()


    async def is_getting_same_message(
            self, 
            chat_history: list[Message],
            timestamp: str = None
            ) -> bool:
    

            if chat_history:
                last_message = chat_history[-1]
                print(f"Last message timestamp: {last_message.messenger_timestamp}, Current timestamp: {timestamp}")

                if str(last_message.messenger_timestamp).strip() == str(timestamp).strip():
                    print("No new messages to process.")
                    return True
            else:
                print("No previous messages found for this user.")
                return False

    async def get_bot_response(
            self,
            messages: List[Message],
            sender_id: str = None,
            ):
        
        """        Get a response from the bot based on the provided messages.
        Args:
            messages (List[Message]): List of messages to process.
            sender_id (str): The ID of the sender.
        Returns:
            str: Response message.
        """
        operator_agent = get_operator_agent()
        response = operator_agent.invoke_with_function_calling(
            messages,
            functions=add_contact_info
        )
        await self.send_message(
            recipient_id=sender_id,
            message_text=response
        )

            
        print(f"Bot response: {response}")
        return response

    async def save_to_gsheet(
            self,
            name: str,
            sender_id: str,
    ):
        """
        Save user information to Google Sheets.
        
        Args:
            name (str): The name of the user.
            sender_id (str): The ID of the sender.
        """
        client_tag_sheet = ClientTagSheet()
        if not client_tag_sheet.has_profle(name):
            client_tag_sheet.add_new_profile(
                profile_name=name,
                user_id=sender_id,
                platform=Platform.MESSENGER
            )
        else:
            client_tag_sheet.update_timestamp(
                profile_name=name
            )


    async def send_message_to_messenger(self, data: MessengerWebhookData):

            if not data.object == "page":
                return Response(status_code=200, content="Data object is not 'page'")
            timestamp = data.get_message_timestamp
            sender_id = data.get_sender_id

            chat_history = ChatHistoryTable()
            messages = chat_history.get_chat_history(sender_id)

            if await self.is_getting_same_message(chat_history=messages, timestamp=timestamp):
                return Response(status_code=200, content="No new messages to process.")

            config_sheet = ConfigSheet()
            is_working_hour = config_sheet.is_working_hour()

            user_table = UserTable()

            for entry in data.entry:
                messaging_events = [
                    event for event in entry.get("messaging", []) if event.get("message")
                ]

                for event in messaging_events:
                    message = event.get("message")
                    sender_id = event["sender"]["id"]
                    profile_name = self.get_user_profile(sender_id)

                    if not messages:
                        messages = []
                    
                    if is_working_hour:
                        messages.append(Message(role="user", content=message["text"]))

                        response = await self.get_bot_response(
                            messages=messages,
                            sender_id=sender_id
                        )
                    else:
                        print("Out of working hours. No response will be sent.")

                    await self.save_to_gsheet(
                        name=profile_name['name'],
                        sender_id=sender_id
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


                    if is_working_hour:
                        chat_history.insert(
                            user_uuid=sender_id,
                            role="assistant",
                            content=response,
                            messenger_timestamp=timestamp
                        )


    async def send_follow_up_message(self, to, messages):
        """
        Send a message via Facebook Messenger using httpx
    
        Args:
            access_token (str): Your Facebook Page access token
            psid (str): Page-scoped ID of the recipient
            message_text (str): The message to send
        
        Returns:
            dict: JSON response from Facebook Graph API
        """
        url = "https://graph.facebook.com/v23.0/me/messages"
    
        # Form data as in the original cURL command
        data = {
            "recipient": f"{{'id':'{to}'}}",
            "messaging_type": "RESPONSE",
            "message": f"{{'text':'{messages}'}}",
            "access_token": self.page_access_token
        }
    
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
        
            response.raise_for_status()
            return response.json()

        
