from pathlib import Path

ROOT_DIR = Path(__file__).parent
CONFIG_FILE = "src/config.yml"
PRICE_SHEET_PATH = ROOT_DIR / "data" / "dental_prices.pdf"
OPERATOR_PROMPT_PATH = ROOT_DIR / "prompts" / "operator_agent_prompt.txt"