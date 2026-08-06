import logging
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Optional

from app.models.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, UserRole
from app.services.auth_service import auth_service

logger = logging.getLogger("autoviva.routes.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegisterRequest, request: Request):
    try:
        # Print raw received body before processing
        raw_body = await request.json()
        logger.info(f"[FastAPI Register Endpoint Received Payload]: {raw_body}")
    except Exception:
        logger.info(f"[FastAPI Register Endpoint Received Model]: {req.model_dump()}")

    try:
        token_resp = auth_service.register_user(req)
        return token_resp
    except ValueError as ve:
        logger.warning(f"Registration validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, request: Request):
    try:
        raw_body = await request.json()
        logger.info(f"[FastAPI Login Endpoint Received Payload]: {raw_body}")
    except Exception:
        logger.info(f"[FastAPI Login Endpoint Received Model]: {req.model_dump()}")

    try:
        token_resp = auth_service.authenticate_user(req)
        return token_resp
    except ValueError as ve:
        logger.warning(f"Login validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header token.")

    token = authorization.split(" ")[1]
    decoded = auth_service.decode_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return UserResponse(
        user_id=decoded["sub"],
        name=decoded["name"],
        email=decoded["email"],
        role=UserRole(decoded["role"])
    )
