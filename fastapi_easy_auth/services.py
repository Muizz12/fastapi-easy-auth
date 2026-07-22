import uuid
import random
import asyncio
from datetime import datetime, timedelta
from typing import Type, Dict, Any, TypeVar, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_easy_auth.config import AuthConfig
from fastapi_easy_auth.models import BaseUserAccount, BaseOTPCode
from fastapi_easy_auth.utils.hashing import get_password_hash, verify_password
from fastapi_easy_auth.utils.jwt import create_access_token
from fastapi_easy_auth.utils.email import send_otp_email_sync

TUser = TypeVar('TUser', bound=BaseUserAccount)
TOTP = TypeVar('TOTP', bound=BaseOTPCode)

def generate_otp() -> str:
    """Generate an 8-digit OTP code."""
    return "".join([str(random.randint(0, 9)) for _ in range(8)])

class AuthManager:
    def __init__(self, config: AuthConfig, user_model: Type[TUser], otp_model: Type[TOTP]):
        """
        Initialize the AuthManager with your configuration and SQLModel classes.
        """
        self.config = config
        self.user_model = user_model
        self.otp_model = otp_model

    async def check_user_exists(self, session: AsyncSession, email: str) -> bool:
        stmt = select(self.user_model).where(self.user_model.email == email.lower().strip())
        res = await session.exec(stmt)
        return res.first() is not None

    async def sign_up(self, session: AsyncSession, email: str, password: Optional[str] = None, extra_fields: Dict[str, Any] = None):
        email_clean = email.lower().strip()
        if await self.check_user_exists(session, email_clean):
            raise ValueError("User already exists with this email")
        
        user_data = {
            "email": email_clean,
            "is_verified": False
        }
        if password:
            user_data["hashed_password"] = get_password_hash(password)
            
        if extra_fields:
            user_data.update(extra_fields)
            
        user = self.user_model(**user_data)
        session.add(user)
        
        otp_code = generate_otp()
        otp_record = self.otp_model(
            email=email_clean,
            code=otp_code,
            type="signup",
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.otp_expire_minutes)
        )
        session.add(otp_record)
        
        await session.commit()
        await session.refresh(user)
        
        asyncio.create_task(
            asyncio.to_thread(
                send_otp_email_sync, 
                self.config, 
                email_clean, 
                otp_code, 
                "your verification code to complete sign up"
            )
        )
        
        return user

    async def sign_in(self, session: AsyncSession, email: str, password: str):
        email_clean = email.lower().strip()
        stmt = select(self.user_model).where(self.user_model.email == email_clean)
        res = await session.exec(stmt)
        user = res.first()
        
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
            
        if not user.is_verified:
            raise ValueError("Email not verified")
            
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            secret_key=self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            expires_delta=timedelta(days=self.config.access_token_expire_days)
        )
        
        refresh_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            secret_key=self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            expires_delta=timedelta(days=self.config.refresh_token_expire_days)
        )
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    async def verify_otp(self, session: AsyncSession, email: str, code: str, otp_type: str = "signup"):
        email_clean = email.lower().strip()
        stmt = select(self.otp_model).where(
            self.otp_model.email == email_clean,
            self.otp_model.code == code,
            self.otp_model.type == otp_type,
            self.otp_model.expires_at > datetime.utcnow()
        )
        res = await session.exec(stmt)
        otp_record = res.first()
        
        if not otp_record:
            raise ValueError("Invalid or expired OTP")
            
        stmt_user = select(self.user_model).where(self.user_model.email == email_clean)
        user = (await session.exec(stmt_user)).first()
        
        if not user:
            raise ValueError("User not found")
            
        if otp_type == "signup":
            user.is_verified = True
            session.add(user)
        
        await session.delete(otp_record)
        await session.commit()
        await session.refresh(user)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            secret_key=self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            expires_delta=timedelta(days=self.config.access_token_expire_days)
        )
        
        return {
            "user": user,
            "access_token": access_token
        }

    async def reset_password_email(self, session: AsyncSession, email: str):
        email_clean = email.lower().strip()
        if not await self.check_user_exists(session, email_clean):
            return True # Fail silently for security
            
        otp_code = generate_otp()
        otp_record = self.otp_model(
            email=email_clean,
            code=otp_code,
            type="recovery",
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.otp_expire_minutes)
        )
        session.add(otp_record)
        await session.commit()
        
        asyncio.create_task(
            asyncio.to_thread(
                send_otp_email_sync, 
                self.config, 
                email_clean, 
                otp_code, 
                "your code to reset your password"
            )
        )
        return True

    async def request_otp(self, session: AsyncSession, email: str, otp_type: str = "signin"):
        """Generate and send an OTP for passwordless login or generic verification."""
        email_clean = email.lower().strip()
        if not await self.check_user_exists(session, email_clean):
            raise ValueError("User not found")
            
        otp_code = generate_otp()
        otp_record = self.otp_model(
            email=email_clean,
            code=otp_code,
            type=otp_type,
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.otp_expire_minutes)
        )
        session.add(otp_record)
        await session.commit()
        
        asyncio.create_task(
            asyncio.to_thread(
                send_otp_email_sync, 
                self.config, 
                email_clean, 
                otp_code, 
                f"your {otp_type} code"
            )
        )
        return True

    async def update_user_password(self, session: AsyncSession, user_id: str, new_password: str):
        stmt = select(self.user_model).where(self.user_model.id == uuid.UUID(user_id))
        user = (await session.exec(stmt)).first()
        if not user:
             raise ValueError("User not found")
             
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        await session.commit()
        return True
