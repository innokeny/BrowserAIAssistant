class UserUseCases:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register_user(self, name: str, email: str):
        user = User(id=None, name=name, email=email)
        return self.user_repository.save(user)
