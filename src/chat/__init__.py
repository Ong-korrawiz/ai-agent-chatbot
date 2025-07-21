from abc import ABC, abstractmethod


class BaseChatApp:

    def __init__(self):
        pass

    @abstractmethod
    def get_bot_response(self, messages: list):
        """
        Get a response based on the provided messages.
        
        Args:
            messages (list): List of messages to process.
        
        Returns:
            str: Response message.
        """
        # Placeholder for actual implementation
        pass
        

    @abstractmethod
    def send_follow_up_message(self, message: str):
        # Placeholder for sending a message
        pass