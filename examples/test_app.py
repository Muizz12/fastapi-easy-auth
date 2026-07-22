import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from fastapi_easy_auth import AuthConfig, AuthManager, BaseUserAccount, BaseOTPCode, get_auth_router

# 1. Define models for our app
class UserAccount(BaseUserAccount, table=True):
    first_name: str = "Test" # Custom field

class OTPCode(BaseOTPCode, table=True):
    pass

# 2. Database setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with async_session_maker() as session:
        yield session

# 3. Setup Auth Library
config = AuthConfig(
    jwt_secret="my_super_secret",
    smtp_host=None, # Will print to console
)
auth_manager = AuthManager(config=config, user_model=UserAccount, otp_model=OTPCode)

# 4. FastAPI Setup
app = FastAPI()
auth_router = get_auth_router(auth_manager, get_session_dependency=get_session)
app.include_router(auth_router, prefix="/auth")

async def test_auth_flow():
    # Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    print("Database initialized.")
    
    # Test Signup
    async with async_session_maker() as session:
        try:
            print("--- Testing Sign Up ---")
            user = await auth_manager.sign_up(session, "test@example.com", "password123", extra_fields={"first_name": "Moiz"})
            print(f"User created: {user.email} (ID: {user.id}), First Name: {user.first_name}")
            
            # Since OTP is sent to thread, give it a moment to print
            await asyncio.sleep(0.5)
            
            # Fetch the OTP from DB manually for testing
            from sqlmodel import select
            otp_record = (await session.exec(select(OTPCode))).first()
            print(f"Retrieved OTP from DB for testing: {otp_record.code}")
            
            print("\n--- Testing OTP Verification ---")
            verify_result = await auth_manager.verify_otp(session, "test@example.com", otp_record.code)
            print(f"Verified! Access Token: {verify_result['access_token'][:20]}...")
            
            print("\n--- Testing Sign In ---")
            signin_result = await auth_manager.sign_in(session, "test@example.com", "password123")
            print(f"Sign In Success! Access Token: {signin_result['access_token'][:20]}...")
            
            print("\nAll tests passed successfully! 🎉")
            
        except Exception as e:
            print(f"Error during test: {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
