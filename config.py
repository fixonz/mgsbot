import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        env_parse_list_separator=","
    )


    # Bot Configuration
    BOT_TOKEN: str = Field(..., validation_alias="BOT_TOKEN")
    ADMIN_IDS_RAW: str = Field(..., validation_alias="ADMIN_IDS")
    
    # Database
    DB_PATH: str = Field(default="bot_database.sqlite", validation_alias="DB_PATH")
    DATABASE_URL: Union[str, None] = Field(default=None, validation_alias="DATABASE_URL")
    
    # Payments
    TATUM_API_KEY: str = Field(..., validation_alias="TATUM_API_KEY")
    LTC_ADDRESSES_RAW: str = Field(..., validation_alias="LTC_ADDRESSES")
    DEPOSIT_TIMEOUT_MINUTES: int = 30

    
    # AI (High-End Features)
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    
    # Web Dashboard
    PORT: int = Field(default=8000, validation_alias="PORT")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    KEEP_ALIVE_URL: str = Field(default="", validation_alias="KEEP_ALIVE_URL")
    DASHBOARD_PIN: str = Field(default="7777", validation_alias="DASHBOARD_PIN")

    @property
    def ADMIN_IDS(self) -> List[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

    @property
    def LTC_ADDRESSES(self) -> List[str]:
        return [x.strip() for x in self.LTC_ADDRESSES_RAW.split(",") if x.strip()]


# Initialize settings
try:
    settings = Settings()
    # Ensure always absolute path
    if not os.path.isabs(settings.DB_PATH):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        settings.DB_PATH = os.path.join(BASE_DIR, settings.DB_PATH)
except Exception as e:
    # Manual fallback for robustness
    from dotenv import load_dotenv
    load_dotenv()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create a settings object with manual fallback values
    settings = Settings(
        BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
        TATUM_API_KEY=os.getenv("TATUM_API_KEY", ""),
        ADMIN_IDS_RAW=os.getenv("ADMIN_IDS", ""),
        LTC_ADDRESSES_RAW=os.getenv("LTC_ADDRESSES", ""),
        DB_PATH=os.path.join(BASE_DIR, os.getenv("DB_PATH", "bot_database.sqlite"))
    )

# Export settings variables for backward compatibility
DB_PATH = settings.DB_PATH
BOT_TOKEN = settings.BOT_TOKEN
ADMIN_IDS = settings.ADMIN_IDS
TATUM_API_KEY = settings.TATUM_API_KEY
LTC_ADDRESSES = settings.LTC_ADDRESSES
DEPOSIT_TIMEOUT_MINUTES = settings.DEPOSIT_TIMEOUT_MINUTES
GEMINI_API_KEY = settings.GEMINI_API_KEY







