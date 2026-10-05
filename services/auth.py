from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from utils.validators import email, text


class Auth:
    def __init__(self, store, secret):
        if len(secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters.")
        self.store, self.secret = store, secret

    def register(self, name, address, password):
        name, address = text(name, "Name", 80), email(address)
        if len(password) < 8 or len(password.encode()) > 72:
            raise ValueError("Password must have at least 8 characters and at most 72 UTF-8 bytes.")
        return self.store.insert("users", {"name": name, "email": address, "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), "created_at": datetime.now(timezone.utc).isoformat()})

    def login(self, address, password):
        users = self.store.find("users", email=email(address))
        if not users or len(password.encode()) > 72 or not bcrypt.checkpw(password.encode(), users[0]["password"].encode()):
            raise ValueError("Email or password is incorrect.")
        now = datetime.now(timezone.utc)
        return jwt.encode({"sub": users[0]["_id"], "iat": now, "exp": now + timedelta(hours=8), "iss": "finance-tracker"}, self.secret, algorithm="HS256")

    def verify(self, token):
        try:
            claims = jwt.decode(token, self.secret, algorithms=["HS256"], issuer="finance-tracker", options={"require": ["sub", "iat", "exp"]})
            users = self.store.find("users", _id=claims["sub"])
            if not users:
                raise ValueError("Account no longer exists.")
            return {k: v for k, v in users[0].items() if k != "password"}
        except jwt.InvalidTokenError as exc:
            raise ValueError("Your session expired. Please sign in again.") from exc
