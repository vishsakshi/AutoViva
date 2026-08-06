import jwt
import time
import uuid
import logging
import pymongo
from passlib.context import CryptContext
from typing import Optional, Dict, Any

from app.core.config import settings
from app.models.auth import UserRegisterRequest, UserLoginRequest, UserResponse, UserRole, TokenResponse

logger = logging.getLogger("autoviva.services.auth")

SECRET_KEY = "autoviva_secret_jwt_key_2026_academic_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400 * 7  # 7 days session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self._init_mongo_client()

    def _init_mongo_client(self):
        try:
            self.mongo_client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.db = self.mongo_client[settings.DB_NAME]
            self.users_col = self.db["users"]
            # Ensure unique index on email
            self.users_col.create_index("email", unique=True)
            logger.info("AuthService connected to MongoDB users collection.")
        except Exception as e:
            logger.warning(f"AuthService Mongo init notice: {e}")
            self.db = None
            self.users_col = None

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: UserResponse) -> str:
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "name": user.name,
            "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return decoded
        except jwt.PyJWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None

    def register_user(self, req: UserRegisterRequest) -> TokenResponse:
        if req.password != req.confirm_password:
            raise ValueError("Password and Confirm Password do not match.")

        email_clean = req.email.strip().lower()

        # Check existing user in MongoDB
        if self.users_col is not None:
            existing = self.users_col.find_one({"email": email_clean})
            if existing:
                raise ValueError("An account with this email address already exists. Please sign in.")

        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        hashed_pwd = self.hash_password(req.password)
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        user_doc = {
            "user_id": user_id,
            "name": req.name.strip(),
            "email": email_clean,
            "hashed_password": hashed_pwd,
            "role": req.role.value,
            "created_at": now
        }

        if self.users_col is not None:
            self.users_col.insert_one(user_doc)
            logger.info(f"Created MongoDB user: {email_clean} (ID: {user_id}, Role: {req.role.value})")

        user_resp = UserResponse(
            user_id=user_id,
            name=user_doc["name"],
            email=user_doc["email"],
            role=UserRole(user_doc["role"])
        )

        token = self.create_access_token(user_resp)
        return TokenResponse(access_token=token, user=user_resp)

    def authenticate_user(self, req: UserLoginRequest) -> TokenResponse:
        email_clean = req.email.strip().lower()

        user_doc = None
        if self.users_col is not None:
            user_doc = self.users_col.find_one({"email": email_clean})

        if not user_doc:
            raise ValueError("No account registered with this email. Please check your email or create an account.")

        if not self.verify_password(req.password, user_doc["hashed_password"]):
            raise ValueError("Incorrect password. Please try again.")

        user_resp = UserResponse(
            user_id=user_doc["user_id"],
            name=user_doc["name"],
            email=user_doc["email"],
            role=UserRole(user_doc["role"])
        )

        token = self.create_access_token(user_resp)
        logger.info(f"Authenticated MongoDB user: {email_clean} (Role: {user_doc['role']})")
        return TokenResponse(access_token=token, user=user_resp)

auth_service = AuthService()
