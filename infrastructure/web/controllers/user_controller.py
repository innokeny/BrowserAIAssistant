from fastapi import APIRouter
from core.use_cases.user_use_cases import UserUseCases
from infrastructure.db.user_repository_impl import UserRepositoryImpl

router = APIRouter()
user_repository = UserRepositoryImpl()
user_use_cases = UserUseCases(user_repository)

@router.post("/users")
def register_user(name: str, email: str):
    return user_use_cases.register_user(name, email)
