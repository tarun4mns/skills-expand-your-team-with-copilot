"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from ..database import teachers_collection

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

_ph = PasswordHasher()


def verify_password(provided_password: str, stored_hash: str) -> bool:
    """Verify a password against a stored Argon2 hash"""
    try:
        return _ph.verify(stored_hash, provided_password)
    except VerifyMismatchError:
        return False

@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})
    
    if not teacher or not verify_password(password, teacher["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }

@router.get("/check-session")
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.find_one({"_id": username})
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }