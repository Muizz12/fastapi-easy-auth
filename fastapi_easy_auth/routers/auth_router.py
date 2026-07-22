from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Callable, Any, Optional

class SignUpRequest(BaseModel):
    email: str
    password: Optional[str] = None

class SignInRequest(BaseModel):
    email: str
    password: str

class VerifyOTPRequest(BaseModel):
    email: str
    code: str
    type: str = "signup"

class RequestOTPRequest(BaseModel):
    email: str
    type: str = "signin"

class ResetPasswordRequest(BaseModel):
    email: str

def get_auth_router(auth_manager, get_session_dependency: Callable[[], Any]) -> APIRouter:
    """
    Returns a FastAPI router with common auth endpoints pre-configured.
    Pass in your auth_manager instance and your FastAPI get_session dependency.
    """
    router = APIRouter()

    @router.post("/signup")
    async def sign_up(request: SignUpRequest, session: AsyncSession = Depends(get_session_dependency)):
        try:
            user = await auth_manager.sign_up(session, request.email, request.password)
            return {"success": True, "message": "OTP sent to email", "user_id": str(user.id)}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.post("/signin")
    async def sign_in(request: SignInRequest, session: AsyncSession = Depends(get_session_dependency)):
        try:
            result = await auth_manager.sign_in(session, request.email, request.password)
            return {
                "success": True,
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"]
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    @router.post("/verify-otp")
    async def verify_otp(request: VerifyOTPRequest, session: AsyncSession = Depends(get_session_dependency)):
        try:
            result = await auth_manager.verify_otp(session, request.email, request.code, request.type)
            return {
                "success": True,
                "access_token": result["access_token"]
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.post("/request-otp")
    async def request_otp(request: RequestOTPRequest, session: AsyncSession = Depends(get_session_dependency)):
        try:
            await auth_manager.request_otp(session, request.email, request.type)
            return {"success": True, "message": "OTP sent to email"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.post("/reset-password-email")
    async def reset_password(request: ResetPasswordRequest, session: AsyncSession = Depends(get_session_dependency)):
        await auth_manager.reset_password_email(session, request.email)
        return {"success": True, "message": "If an account exists, a reset link/OTP has been sent."}

    return router
