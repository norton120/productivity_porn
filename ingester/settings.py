from pydantic_settings import BaseSettings
from enum import Enum

class BlockSize(str, Enum):
    small = "small"
    medium = "medium"
    big = "big"


class Settings(BaseSettings):
    """Settings for the application"""
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    #slack_api_token: str
    #slack_user_id: str
    #calendar_email:str
    atlassian_token: str
    atlassian_email: str
    atlassian_host: str
    sync_dir: str