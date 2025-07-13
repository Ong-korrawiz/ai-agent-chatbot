from openai import OpenAI
import json
from typing import List, Dict, Any, Optional, Union

from pydantic import BaseModel
from src.utils.common import ConfigUtils
from src._types import Message


class BaseAgent:
    """
    A client class for interacting with OpenAI's API, supporting both regular prompts
    and function calling capabilities.
    """
    
    def __init__(
            self,
            api_key: str = ConfigUtils.get_env("OPENAI_API_KEY"),
            model: str = "gpt-4o",  # Default model, can be changed to gpt-4 or others
            temperature: float = 0.7,  # Default temperature for creativity level
            system_prompt: Optional[str] = None
            ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (str): Your OpenAI API key
            model (str): The model to use (default: gpt-4)
        """
        self.client = OpenAI(
            api_key=api_key,
            )
        self.model = model
        self.messages: List[Message] = []
        self.system_prompt = self.set_system_prompt(
            system_prompt=system_prompt
            )
        self.temperature = temperature

    def set_system_prompt(self, system_prompt: str):
        """
        Set the system prompt for the OpenAI client.

        Args:
            system_prompt (str): The system prompt to set context
        """
        self.system_prompt = system_prompt
        if system_prompt:
            self.messages.append(Message(role="system", content=system_prompt))


    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the list of messages in the conversation.
        
        Returns:
            List[Dict[str, Any]]: List of messages with role and content
        """
        return self.messages
    
    def get_dict_messages(self) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Convert the messages to a format suitable for OpenAI API.
        
        Returns:
            List[Dict[str, Union[str, List[Dict[str, str]]]]]: List of messages with role and content
        """
        if not self.messages:
            return []
        messages = self.get_messages()
        return [{"role": msg.role, "content": msg.content} for msg in messages]


    def invoke(
            self,
            input_messages: list[dict],
            )-> str:
        """
        Send a regular prompt to OpenAI API and return the response.
        
        Args:
            prompt (str): The user prompt/message
            system_message (str, optional): System message to set context
            max_tokens (int, optional): Maximum tokens in response
            temperature (float): Creativity level (0.0 to 2.0)
            
        Returns:
            str: The AI's response content
            
        Raises:
            Exception: If API call fails
        """
        messages = self.get_dict_messages()
        messages.extend(
            [{"role": msg.role, "content": msg.content} for msg in input_messages]
        )
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=messages,
                temperature=self.temperature,
            )

            return response.output_text

        except Exception as e:
            raise Exception(f"Error calling OpenAI API: {str(e)}")

