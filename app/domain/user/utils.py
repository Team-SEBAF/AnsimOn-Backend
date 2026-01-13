import base64
import hashlib
import hmac


def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    msg = username + client_id
    digest = hmac.new(
        key=client_secret.encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode()
