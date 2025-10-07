import base64
from datetime import datetime, timezone


def generate_auth(consumer_key, consumer_secret):
    raw = f"{consumer_key}:{consumer_secret}"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("utf-8")

    print(b64)       

    return {"Authorization": f"Basic {b64}"}
    

def generate_timestamp(now=None):
    """
    Return timestamp in format YYYYMMDDHHMMSS (UTC).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%d%H%M%S")


def generate_STKpassword(shortcode, passkey, timestamp=None):
    """
    Generate Base64-encoded password = Base64(shortcode + passkey + timestamp).
    """
    if timestamp is None:
        timestamp = generate_timestamp()

    raw = f"{shortcode}{passkey}{timestamp}"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
    return b64
