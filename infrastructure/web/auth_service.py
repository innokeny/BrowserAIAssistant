from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from infrastructure.db.db_connection import get_redis_client
from core.repositories.user_repository_impl import UserRepositoryImpl
from core.entities.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    def __init__(self):
        self.user_repository = UserRepositoryImpl()
        self.redis_client = get_redis_client()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = "your-secret-key"  # В продакшене использовать безопасный ключ
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        
        # Store token in Redis
        self.redis_client.setex(
            f"token:{encoded_jwt}",
            int(expires_delta.total_seconds()) if expires_delta else 900,  # 15 minutes in seconds
            str(data.get("user_id", ""))
        )
        
        return encoded_jwt

    def register_user(self, name: str, email: str, password: str):
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            return None, "Email already registered"

        user = User(
            id=None,  
            name=name,
            email=email,
            password_hash=self.get_password_hash(password),
            user_role="user"  
        )
        
        user = self.user_repository.save(user)
        if not user:
            return None, "Failed to create user"

        access_token = self.create_access_token(
            data={
                "sub": str(user.id), 
                "user_id": user.id, 
                "email": user.email,
                "user_role": user.user_role
            }
        )

        return {"access_token": access_token, "token_type": "bearer"}, None

    def authenticate_user(self, email: str, password: str):
        user = self.user_repository.get_by_email(email)
        if not user:
            return None, "User not found"

        if not self.verify_password(password, user.password_hash):
            return None, "Incorrect password"

        access_token = self.create_access_token(
            data={
                "sub": str(user.id), 
                "user_id": user.id, 
                "email": user.email,
                "user_role": user.user_role
            }
        )

        return {"access_token": access_token, "token_type": "bearer"}, None

    def validate_token(self, token: str):
        try:
            try:
                payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            except jwt.ExpiredSignatureError:
                self.redis_client.delete(f"token:{token}")
                return None, "Token has expired"
            except jwt.JWTError:
                return None, "Invalid token"

            if not self.redis_client.exists(f"token:{token}"):
                return None, "Token has expired"

            user_id = payload.get("user_id")
            if not user_id:
                return None, "Invalid token payload"

            user = self.user_repository.get_by_id(user_id)
            if not user:
                return None, "User not found"

            return user, None

        except Exception:
            return None, "Invalid token"

    async def get_current_user_id(self, token: str = Depends(oauth2_scheme)) -> int:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id = payload.get("user_id")
            if user_id is None:
                raise credentials_exception
            return int(user_id)
        except JWTError:
            raise credentials_exception

auth_service = AuthService()

async def get_current_user(authorization: str = Header(None)):
    """Get the current authenticated user from the authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    user, error = auth_service.validate_token(token)
    
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return user