from core.repositories.user_repository import UserRepository
from core.entities.user import User

class UserRepositoryImpl(UserRepository):
    def save(self, user):
        # Логика сохранения пользователя в базу данных
        return User(id=1, name=user.name, email=user.email)
