from pydantic import BaseModel

class Message(BaseModel):

    role: str
    content: str 
    messenger_timestamp: str | None = None

# Request Models.
class MessengerWebhookRequestData(BaseModel):
    object: str = ""
    entry: list = []
    previous_timestamp: str | None = None

    @property
    def get_sender_id(self) -> str: 
        if self.object == 'page':
            for entry in self.entry:
                messaging_events = [
                    event for event in entry.get("messaging", []) if event.get("message")
                ]
                if messaging_events:
                    return messaging_events[0]["sender"]["id"]
        return None
    
    @property
    def get_message_timestamp(self) -> str:
        if not self.object == "page":
            return None
        for entry in self.entry:
            messaging_events = [
                event for event in entry.get("messaging", []) if event.get("message")
            ]
            if messaging_events:
                return messaging_events[0]["timestamp"]
        return None

    def is_same_timestamp(self, timestamp: str) -> bool:
        """
        Check if the current timestamp is the same as the provided timestamp.
        """
        if not self.previous_timestamp:
            self.previous_timestamp = timestamp
            return False

        return self.get_message_timestamp() == timestamp
    