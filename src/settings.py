import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ROOT_DIR = Path(__file__).parent
CONFIG_FILE = "src/config.yml"
PRICE_SHEET_PATH = ROOT_DIR / "data" / "dental_prices.pdf"
OPERATOR_PROMPT_PATH = ROOT_DIR / "prompts" / "operator_agent_prompt.txt"

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "your-project-id:your-region:your-instance")
DB_USER = os.getenv("DB_USER", "your-username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your-password")
DB_NAME = os.getenv("DB_NAME", "your-database")
GOOGLE_API_CRED = os.getenv('GOOGLE_API_CRED')

GCP_CREDENTIALS = ROOT_DIR / "creads.json"
FUNCTION_CALLINGS_FILE = ROOT_DIR / "prompts/functions.json"

LINE_CHANNEL_ACCESS_TOKEN=os.getenv('LINE_CHANNEL_ACCESS_TOKEN').replace('"','')
LINE_CHANNEL_SECRET=os.getenv('LINE_CHANNEL_SECRET').replace('"', '')

MESSENGER_VERIFY_TOKEN = os.getenv('MESSENGER_WEBHOOK_TOKEN').replace('"', '')

