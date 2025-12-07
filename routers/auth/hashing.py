from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash:
    @staticmethod
    def hash(password: str):
        return bcrypt_context.hash(password)

    @staticmethod
    def verify(password: str, hashed: str):
        return bcrypt_context.verify(password, hashed)
