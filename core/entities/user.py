class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str = None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
