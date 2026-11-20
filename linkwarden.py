import json
import re
import subprocess
import sys
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


KEYRING_ATTRIBUTES = ("application", "bakugo.linkwarden", "purpose", "connection")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._~+/=-]{1,4096}")


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def keyring(*args, secret=""):
    return subprocess.run(
        ("/usr/bin/secret-tool", *args, *KEYRING_ATTRIBUTES),
        input=secret,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def server_origin(value):
    if len(value) > 300 or re.search(r"[^!-~]|[\\%?#]", value):
        return None
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.path not in ("", "/")
        or port == 0
        or not re.fullmatch(r"[A-Za-z0-9.\-]+(?::[0-9]+)?|\[[0-9a-fA-F:]+\](?::[0-9]+)?", parsed.netloc)
    ):
        return None
    return f"https://{parsed.netloc.lower()}"


def store_connection(value):
    try:
        settings = json.loads(value)
        server = server_origin(settings["server"].strip())
        token = settings["token"].strip()
    except (ValueError, KeyError, TypeError, AttributeError):
        return "invalidToken"
    if server is None:
        return "invalidServer"
    if not TOKEN_PATTERN.fullmatch(token):
        return "invalidToken"

    secret = json.dumps({"server": server, "token": token})
    try:
        result = keyring("store", "--label", "Linkwarden for Omarchy", secret=secret)
    except (OSError, subprocess.TimeoutExpired):
        return "keyring"
    return "stored" if result.returncode == 0 else "keyring"


def valid_url(value):
    if len(value) > 2048 or re.search(r"\s|[\x00-\x1f\x7f\\]", value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.hostname)
        and parsed.username is None
        and (port is None or port > 0)
    )


def save_link(url):
    if not valid_url(url):
        return "invalidUrl"
    try:
        result = keyring("lookup")
    except (OSError, subprocess.TimeoutExpired):
        return "keyring"
    if result.returncode != 0:
        return "keyring" if result.stderr else "missing"
    try:
        settings = json.loads(result.stdout)
        server = server_origin(settings["server"])
        token = settings["token"]
        if server is None or not TOKEN_PATTERN.fullmatch(token):
            return "missing"
    except (ValueError, KeyError, TypeError):
        return "missing"

    request = Request(
        f"{server}/api/v1/links",
        data=json.dumps({"url": url, "collection": {"name": "Unorganized"}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with build_opener(RejectRedirects()).open(request, timeout=45) as response:
            body = response.read(65537)
        if len(body) > 65536:
            return "unconfirmed"
        payload = json.loads(body)
        link = payload["response"]
        if type(link["id"]) is not int or link["id"] <= 0:
            return "unconfirmed"
        collection = link.get("collection")
        if isinstance(collection, dict) and collection.get("name") == "Unorganized":
            return "saved"
        return "destination"
    except HTTPError as error:
        with error:
            return {
                400: "rejected",
                401: "unauthorized",
                403: "unauthorized",
                409: "duplicate",
                429: "busy",
            }.get(error.code, "unconfirmed")
    except (URLError, HTTPException, OSError, ValueError, KeyError, TypeError):
        return "unconfirmed"


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    value = sys.stdin.readline(8192).strip()
    if action == "store":
        print(store_connection(value))
    elif action == "save":
        print(save_link(value))
