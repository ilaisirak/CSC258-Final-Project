# Defines the HTTP endpoints for the user service.
# All routes are async and use the get_db dependency for database access.

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserSignIn, UserResponse

router = APIRouter()

# Returns the currently authenticated user by reading their UUID from
# the X-User-Id request header. Returns None if the header is absent,
# which the frontend treats as an unauthenticated state.
# Note: this is a simplified session mechanism. A production implementation
# would use JWT tokens instead of a plain user ID header.
@router.get("/users/me", response_model=UserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Looks up a user by name and role combination.
# Returns 404 if no matching user is found.
# Note: this is a placeholder sign-in mechanism for development.
# A production implementation would verify a password hash.
@router.post("/users/sign-in", response_model=UserResponse)
async def sign_in(payload: UserSignIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.name == payload.name, User.role == payload.role)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Stateless sign-out endpoint. Since authentication is currently handled
# via a header rather than a server-side session, no state needs to be
# cleared on the backend — the frontend is responsible for dropping the token.
@router.post("/users/sign-out")
async def sign_out():
    return {"message": "Signed out"}

# Retrieve all registered users.
# Used by the class roster and add-student flows.
@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# Retrieve a single user by their UUID.
# Called by other services that need to resolve a user ID to a name or role.
# Returns 404 if no user with the given ID exists.
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Register a new user account.
# Checks for an existing account with the same email before inserting,
# returning 409 Conflict if a duplicate is found.
@router.post("/users", response_model=UserResponse)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user