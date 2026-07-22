# FastAPI Easy Auth - Full Integration Guide 🚀

This guide explains how to install and integrate the `fastapi-easy-auth` module into any of your new projects from scratch. It handles both standard (password-based) and **passwordless** authentication out of the box!

---

## Step 1: Installation

Since you have built this as a local, reusable library, you can install it directly into your new project's virtual environment using `pip`.

Open your terminal, navigate to your new project's directory, and run:
```bash
# This installs your package directly from GitHub
pip install git+https://github.com/Muizz12/fastapi-easy-auth.git
```

---

## Step 2: Set Up Environment Variables

Create a `.env` file in the root of your new project. This ensures you never hardcode secrets or email passwords directly in your python files.

**`.env`**
```env
# Essential
JWT_SECRET=your_super_secret_jwt_key_here

# Optional: Real SMTP Email Details (If left out, it will print OTPs to the console)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_secure_app_password
FROM_EMAIL=noreply@yourdomain.com
```

---

## Step 3: Write Your Code (`main.py`)

Here is the complete boilerplate to integrate the authentication module into a new FastAPI app.

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, Field
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 1. Import everything you need from the library
from fastapi_easy_auth import (
    AuthConfig, 
    AuthManager, 
    BaseUserAccount, 
    BaseOTPCode, 
    get_auth_router
)

# Load environment variables
load_dotenv()

# ==========================================
# Database Configuration
# ==========================================
DATABASE_URL = "sqlite+aiosqlite:///./my_new_project.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    """Provides the DB session to FastAPI routes."""
    async with async_session_maker() as session:
        yield session

# ==========================================
# Define Your Custom Models
# ==========================================
# Inherits basic fields: id, email, hashed_password (optional), is_verified
class UserAccount(BaseUserAccount, table=True):
    # Add any custom fields unique to this specific project!
    first_name: str | None = None
    last_name: str | None = None

# Inherits OTP features: email, code, type, expires_at
class OTPCode(BaseOTPCode, table=True):
    pass

# ==========================================
# Configure AuthManager
# ==========================================
# Load credentials from the .env file automatically
auth_config = AuthConfig(
    jwt_secret=os.getenv("JWT_SECRET", "fallback-secret"),
    smtp_host=os.getenv("SMTP_HOST"),
    smtp_port=int(os.getenv("SMTP_PORT")) if os.getenv("SMTP_PORT") else None,
    smtp_user=os.getenv("SMTP_USER"),
    smtp_password=os.getenv("SMTP_PASSWORD"),
    from_email=os.getenv("FROM_EMAIL", "noreply@domain.com")
)

# Initialize the manager
auth_manager = AuthManager(
    config=auth_config, 
    user_model=UserAccount, 
    otp_model=OTPCode
)

# ==========================================
# Initialize FastAPI App
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan, title="My App Auth")

# Mount the pre-built auth router!
app.include_router(
    get_auth_router(auth_manager, get_session_dependency=get_db_session),
    prefix="/auth",
    tags=["Authentication"]
)
```

---

## Step 4: Run Your Server

Start your server normally:
```bash
uvicorn main:app --reload
```

---

## Step 5: How the APIs Work

By adding that `get_auth_router` line, your app instantly has 5 powerful API endpoints. Here is how your frontend should use them depending on your desired flow.

### Option A: The Standard Flow (With Passwords)

1. **Sign Up:** `POST /auth/signup`
   ```json
   {
     "email": "user@example.com",
     "password": "mySecurePassword123"
   }
   ```
2. **Verify Email:** `POST /auth/verify-otp` (Use the code sent to their email)
   ```json
   {
     "email": "user@example.com",
     "code": "48745816",
     "type": "signup"
   }
   ```
   *(Returns JWT Token automatically!)*
3. **Future Sign Ins:** `POST /auth/signin`
   ```json
   {
     "email": "user@example.com",
     "password": "mySecurePassword123"
   }
   ```

### Option B: The Passwordless Flow (Magic Link / OTP)

1. **Sign Up:** `POST /auth/signup`
   *(Leave the password field completely out)*
   ```json
   {
     "email": "user@example.com"
   }
   ```
2. **Verify & Initial Sign In:** `POST /auth/verify-otp`
   ```json
   {
     "email": "user@example.com",
     "code": "48745816",
     "type": "signup"
   }
   ```
   *(Returns JWT Token automatically!)*
3. **Future Sign Ins:** 
   Since they don't have a password, they first request an OTP:
   **`POST /auth/request-otp`**
   ```json
   {
     "email": "user@example.com",
     "type": "signin"
   }
   ```
   They then submit the code they received via email:
   **`POST /auth/verify-otp`**
   ```json
   {
     "email": "user@example.com",
     "code": "88822211",
     "type": "signin"
   }
   ```
   *(Returns new JWT Token!)*

### Password Reset 
1. **Request Reset:** `POST /auth/reset-password-email`
   ```json
   { "email": "user@example.com" }
   ```
2. **Verify Reset:** `POST /auth/verify-otp` (Using `type: "recovery"`)
