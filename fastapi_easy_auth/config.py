from typing import Optional
from pydantic_settings import BaseSettings

class AuthConfig(BaseSettings):
    """
    Configuration for the fastapi-easy-auth library.
    Pass an instance of this to the AuthManager upon initialization.
    """
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 7
    refresh_token_expire_days: int = 30
    otp_expire_minutes: int = 10
    
    # SMTP details for sending emails
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
