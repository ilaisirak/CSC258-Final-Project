from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserSignIn, UserResponse

router = APIRouter()

# Called by AuthContext on every page load to restore session
@router.get("/users/me", response_model=UserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Called by AuthContext.signIn
@router.post("/users/sign-in", response_model=UserResponse)
async def sign_in(payload: UserSignIn, db: AsyncSession = Depends(get_db)):
    # For now, look up by name + role. Once you add passwords this changes.
    result = await db.execute(
        select(User).where(User.name == payload.name, User.role == payload.role)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Called by AuthContext.signOut — stateless for now
@router.post("/users/sign-out")
async def sign_out():
    return {"message": "Signed out"}

# Get all users — used by roster/add student flows
@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# Get a single user by ID — called by other services
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Create a user
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