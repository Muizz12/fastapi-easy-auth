# FastAPI Easy Auth 🚀

A highly reusable, plug-and-play Authentication library for FastAPI and SQLModel. 

This library was extracted to save you from re-writing the same authentication logic (Sign Up, Sign In, OTP Verification, Password Resets) across multiple projects. It handles JWT generation, password hashing (bcrypt), OTP workflows, and database interactions out of the box.

## Installation

Since this is a local package, you can install it in any of your new Python virtual environments by pointing pip to its directory:

```bash
# This installs your package directly from GitHub
pip install git+https://github.com/Muizz12/fastapi-easy-auth.git
```

---

## Complete Usage Example

Below is a complete, single-file example showing how you would integrate `fastapi-easy-auth` into a brand new project.

### 1. The Code (`main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, Field
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# Import everything you need from the library
from fastapi_easy_auth import (
    AuthConfig, 
    AuthManager, 
    BaseUserAccount, 
    BaseOTPCode, 
    get_auth_router
)

# ---------------------------------------------------------
# 1. Database Setup
# ---------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///./my_new_project.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    """Dependency to provide the DB session to FastAPI routes."""
    async with async_session_maker() as session:
        yield session

# ---------------------------------------------------------
# 2. Define Your Models
# ---------------------------------------------------------
# Inherit from BaseUserAccount to get 'email', 'hashed_password', 'is_verified'.
# You can add as many custom fields as your specific project needs!
class UserAccount(BaseUserAccount, table=True):
    first_name: str = Field(default="Unknown")
    last_name: str = Field(default="Unknown")
    phone_number: str | None = None

# Inherit from BaseOTPCode to get OTP tracking features
class OTPCode(BaseOTPCode, table=True):
    pass

# ---------------------------------------------------------
# 3. Configure the Library
# ---------------------------------------------------------
# Set up your JWT secrets and SMTP email credentials.
# If you leave SMTP fields empty (None), the library enters "Simulation Mode"
# and prints OTPs to your console (perfect for local development).
auth_config = AuthConfig(
    jwt_secret="your_super_secret_jwt_key_here",
    access_token_expire_days=7,
    
    # SMTP Details (Fill these in for production emails)
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
    from_email="noreply@yourdomain.com"
)

# Initialize the AuthManager with your models and config
auth_manager = AuthManager(
    config=auth_config, 
    user_model=UserAccount, 
    otp_model=OTPCode
)

# ---------------------------------------------------------
# 4. FastAPI Setup
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan, title="My New Project API")

# Mount the pre-built router!
# This automatically creates /signup, /signin, /verify-otp, and /reset-password-email routes
app.include_router(
    get_auth_router(auth_manager, get_session_dependency=get_db_session),
    prefix="/auth",
    tags=["Authentication"]
)

@app.get("/")
def read_root():
    return {"message": "Welcome to my new project!"}
```

### 2. Running Your Project

Start your FastAPI server normally:
```bash
uvicorn main:app --reload
```

### 3. The APIs You Automatically Get

By mounting `get_auth_router`, your app instantly has the following fully functional endpoints available at `http://localhost:8000/docs`:

1. **`POST /auth/signup`**
   - **Body:** `{"email": "user@example.com", "password": "securepassword"}`
   - **Action:** Hashes the password, saves the user (unverified), generates an OTP, and sends the welcome email.

2. **`POST /auth/verify-otp`**
   - **Body:** `{"email": "user@example.com", "code": "12345678", "type": "signup"}`
   - **Action:** Verifies the code, marks the user as `is_verified=True`, and returns the first JWT Access Token.

3. **`POST /auth/signin`**
   - **Body:** `{"email": "user@example.com", "password": "securepassword"}`
   - **Action:** Checks credentials, ensures the email is verified, and returns `{ "access_token": "...", "refresh_token": "..." }`.

4. **`POST /auth/reset-password-email`**
   - **Body:** `{"email": "user@example.com"}`
   - **Action:** Generates a new OTP of type `recovery` and emails it to the user.

---

## Advanced Usage (GraphQL / Custom Routes)

If you don't want to use the pre-built REST router (for instance, if you are building a **GraphQL** API with Strawberry), you can just call the `auth_manager` directly inside your mutations!

```python
import strawberry
from sqlmodel.ext.asyncio.session import AsyncSession

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def sign_up(self, email: str, password: str, first_name: str) -> str:
        # Get your DB session however your GraphQL context handles it
        session = ... 
        
        # Call the library's core function! 
        # (Pass extra fields dict to populate your custom table columns)
        user = await auth_manager.sign_up(
            session=session, 
            email=email, 
            password=password,
            extra_fields={"first_name": first_name}
        )
        return "Success! Check your email for the OTP."
```
