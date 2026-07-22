from typing import Optional
from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field

class BaseUserAccount(SQLModel):
    """
    Base class for UserAccount.
    Inherit from this and add `table=True` in your application.
    You can also add custom fields like first_name, last_name, etc.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BaseOTPCode(SQLModel):
    """
    Base class for OTPCode.
    Inherit from this and add `table=True` in your application.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True)
    code: str
    type: str = Field(default="signup")
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
