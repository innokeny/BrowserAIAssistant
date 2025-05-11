class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str = None, user_role: str = "user"):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.user_role = user_role
