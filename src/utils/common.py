import yaml
import os

from src.settings import CONFIG_FILE


class ConfigUtils:
    """
    Utility class for configuration management.
    Provides methods to load and save configuration data.
    """

    @staticmethod
    def load_config(file_path: str = CONFIG_FILE) -> dict:
        """
        Load configuration from a YAML file.

        Args:
            file_path (str): Path to the YAML configuration file.

        Returns:
            dict: Configuration data as a dictionary.
        """
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    @staticmethod
    def get_env(key: str, default=None) -> str:
        """
        Get an environment variable value.

        Args:
            key (str): The name of the environment variable.
            default: Default value if the environment variable is not set.

        Returns:
            str: The value of the environment variable or default value.
        """
        return os.getenv(key, default)
    
class CommonUtils:

    @staticmethod
    def is_folder_empty(folder_path):
        """
        Checks if a folder is empty.

        Parameters:
        folder_path (str): The path to the folder.

        Returns:
        bool: True if the folder is empty, False otherwise.
        """
        if not os.path.isdir(folder_path):
            return False    
        return len(os.listdir(folder_path)) == 0