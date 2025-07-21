import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.agents.base_agent import BaseAgent
from src.utils.loader import PdfFile
from src.utils.common import ConfigUtils, CommonUtils
from src.settings import CONFIG_FILE, PRICE_SHEET_PATH, OPERATOR_PROMPT_PATH
from src.gcp.drive import GoogleDrive
  # Adjust the path as needed


def get_operator_agent() -> BaseAgent:
    """
    Create and return an instance of the operator agent.
    The agent is configured with a system prompt and a price sheet.
    """
    # Load configuration
    config = ConfigUtils.load_config(file_path=CONFIG_FILE)
    
    # Load the price sheet
    if CommonUtils.is_folder_empty(PRICE_SHEET_PATH.parent):
        google_drive = GoogleDrive()
        file = google_drive.download_file(
            file_id="1fFL7FWeYu1lxeVxg2jc6msngAeFDnvs9",
            target_folder="src/data"
        )

    pdf_file = PdfFile(file_path=PRICE_SHEET_PATH)
    price_sheet_content = pdf_file.get_markdown()
    
    # Load the operator prompt
    with open(OPERATOR_PROMPT_PATH, 'r', encoding='utf-8') as file:
        system_prompt = file.read().format(price_sheet=price_sheet_content)
    
    # Create the operator agent
    operator_agent = BaseAgent(
        model=config.get('model', 'gpt-4o-mini-2024-07-18'),
        temperature=config.get('temperature', 0),
        system_prompt=system_prompt
    )
    
    return operator_agent

