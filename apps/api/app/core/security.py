from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$RtQIC/DQwbsIHvcNUrkAqQ$"
    "pL26G/jtVnaGr8ykEYEbvt1ibiQp8FDPGViBO0Uxunk"
)


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    return verify_password(password, password_hash or DUMMY_HASH)
