from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from infrastructure.db.user_repository_impl import UserRepositoryImpl
from infrastructure.db.resource_manager import ResourceManager
from infrastructure.db.db_connection import get_redis_client

class AuthService:
    def __init__(self):
        self.user_repository = UserRepositoryImpl()
        self.resource_manager = ResourceManager()
        self.redis_client = get_redis_client()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = "your-secret-key"  # In production, use environment variable
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def register_user(self, name: str, email: str, password: str):
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            return None, "Email already registered"

        # Create new user
        from core.entities.user import User
        user = User(
            id=None,  # ID will be assigned by the database
            name=name,
            email=email,
            password_hash=self.get_password_hash(password)
        )
        
        # Save user with hashed password
        user = self.user_repository.save(user)
        if not user:
            return None, "Failed to create user"

        # Create default quotas for the user
        self.resource_manager.create_default_quotas(user.id)

        # Generate access token
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        # Store token in Redis with expiration
        self.redis_client.setex(
            f"token:{access_token}",
            self.access_token_expire_minutes * 60,
            str(user.id)
        )

        return access_token, None

    def authenticate_user(self, email: str, password: str):
        user = self.user_repository.get_by_email(email)
        if not user:
            return None, "User not found"

        if not self.verify_password(password, user.password_hash):
            return None, "Incorrect password"

        # Generate access token
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        # Store token in Redis with expiration
        self.redis_client.setex(
            f"token:{access_token}",
            self.access_token_expire_minutes * 60,
            str(user.id)
        )

        return access_token, None

    def validate_token(self, token: str):
        try:
            # Check if token exists in Redis
            if not self.redis_client.exists(f"token:{token}"):
                return None, "Invalid token"

            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if not user_id:
                return None, "Invalid token payload"

            # Get user from database
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return None, "User not found"

            return user, None

        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.JWTError:
            return None, "Invalid token" 