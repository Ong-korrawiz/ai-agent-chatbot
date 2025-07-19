import json
from src.settings import FUNCTION_CALLINGS_FILE

class FunctionCallingUtils:
    @staticmethod
    def load_schema(func_name: str) -> dict:
        """
        Load functions calling configuration from a JSON file.
        """
        try:
            with open(FUNCTION_CALLINGS_FILE, 'r') as file:
                functions_calling = json.load(file)
                return functions_calling.get(func_name, {})
        except FileNotFoundError:
            print("functions_calling.json file not found.")
            return {}
        except json.JSONDecodeError:
            print("Error decoding JSON from functions_calling.json.")
            return {}
        

FunctionCallingUtils.load_schema(
    "add_contact_info"
)