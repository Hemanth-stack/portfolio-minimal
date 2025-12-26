from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_session_token(username: str) -> str:
    settings = get_settings()
    serializer = URLSafeTimedSerializer(settings.secret_key)
    return serializer.dumps({"username": username}, salt="session")


def verify_session_token(token: str, max_age: int = 86400 * 7) -> dict | None:
    """Verify session token. Default max_age is 7 days."""
    settings = get_settings()
    serializer = URLSafeTimedSerializer(settings.secret_key)
    try:
        data = serializer.loads(token, salt="session", max_age=max_age)
        return data
    except Exception:
        return None
