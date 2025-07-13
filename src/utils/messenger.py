from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from typing import List
import uvicorn
import httpx
import os



class Messenger:
# Helpers.
    def __init__(self, page_access_token: str = None):
        if not page_access_token:
            self.page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").replace('"', '')

        else:
            self.page_access_token = page_access_token

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
            "https://graph.facebook.com/v2.6/me/messages",
            params={"access_token": page_access_token},
            headers={"Content-Type": "application/json"},
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
            params={"access_token": self.page_access_token, "fields": "name,picture"},
        )
        response.raise_for_status()
        return response.json()


