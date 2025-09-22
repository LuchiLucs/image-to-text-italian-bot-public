import os
from dotenv import load_dotenv
from pydantic import SecretStr
import logging

# Setup logging
logger = logging.getLogger("bot")
logger.setLevel("INFO")
logging.basicConfig(format="[%(asctime)s - %(levelname)s] %(message)s")

# Setup .env file
_current_dir = os.path.dirname(__file__)
_env_path = os.path.join(_current_dir, "../../.env")
load_dotenv()
logger.info(f"Loading .env file from: {_env_path}")

# Get tokens from environment variables
TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_TOKEN"
)  # TELEGRAM_TOKEN | TEST_TELEGRAM_TOKEN
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN or TEST_TELEGRAM_TOKEN must be set in .env file")
TELEGRAM_TOKEN = str(
    TELEGRAM_TOKEN
)  # or use: TELEGRAM_TOKEN = TELEGRAM_TOKEN  # type: ignore

AZURE_OPENAI_API_KEY = os.environ.get(
    "AZURE_OPENAI_API_KEY"
)  # AZURE_OPENAI_API_KEY | OPENAI_API_KEY
AZURE_OPENAI_API_KEY = SecretStr(AZURE_OPENAI_API_KEY) if AZURE_OPENAI_API_KEY else None

# Optional: Whitelist of allowed groups (group chat IDs)
ALLOWED_GROUP_IDS = (
    [int(x) for x in os.environ.get("ALLOWED_GROUP_IDS", "").split(",")]
    if os.environ.get("ALLOWED_GROUP_IDS")
    else []
)
BOT_PRIVACY_MODE_ON = False
