import bcrypt

BCRYPT_ROUNDS = 12
MAX_PASSWORD_BYTES = 72

def hash_password(plain: str) -> str:
    data = plain.encode("utf-8")
    if len(data) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(data, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    data = plain.encode("utf-8")
    if len(data) > MAX_PASSWORD_BYTES:
        # No stored password can be this long, so it can never match.
        return False
    try:
        return bcrypt.checkpw(data, hashed.encode("utf-8"))
    except ValueError:
        # Stored hash is malformed; treat as a failed login, not a 500 error.
        return False