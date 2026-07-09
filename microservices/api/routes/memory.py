from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from infrastructure.database.session import db
from memory.long_term.service import LongTermMemory
from middleware.auth import verify_token

router = APIRouter(prefix="/memory", tags=["Memory"])


class UserProfileResponse(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    user_type: str = "visitor"


class UserProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    company: str | None = None
    company_address: str | None = None
    preferred_meeting_type: str | None = None
    preferred_timezone: str | None = None


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, token_user: dict = Depends(verify_token)):
    async with db.session_factory() as session:
        memory = LongTermMemory(session)
        profile = await memory.get_user_by_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return UserProfileResponse(
            id=str(profile.id),
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            company=profile.company,
            user_type=profile.user_type,
        )


@router.patch("/profile/{user_id}")
async def update_user_profile(
    user_id: str,
    updates: UserProfileUpdate,
    token_user: dict = Depends(verify_token),
):
    async with db.session_factory() as session:
        memory = LongTermMemory(session)
        await memory.update_user_profile(user_id, updates.model_dump(exclude_none=True))
        return {"status": "updated"}
