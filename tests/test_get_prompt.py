from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.prompts_utils import get_prompt
from settings import PRICE_SHEET_PATH, OPERATOR_PROMPT_PATH
from utils.loader import PdfFile

if __name__ == "__main__":
    # Example usage of get_prompt function
    txt_path = OPERATOR_PROMPT_PATH  # Path to the prompt text file
    price_sheet_content = PdfFile(file_path=PRICE_SHEET_PATH).get_markdown() 
    formatted_prompt = get_prompt(txt_path, price_sheet=price_sheet_content)
    
    # Print the formatted prompt
    print(formatted_prompt)