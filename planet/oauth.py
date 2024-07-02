import base64
import hashlib
from http import server
import httpx
import random
import socket
import threading
from typing import Tuple
import webbrowser
from urllib import parse
import time


def login_auth_code_flow() -> Tuple[str, str]:
    '''Do an oauth code flow with login, returning an access and refresh token'''

    def b64(b): return str(base64.urlsafe_b64encode(b), encoding="ascii").rstrip("=")

    issuer = "https://login.planet.com"
    client_id = "LpuNO3w4djMCvVqVHfMSiHMyeBYYflUS"
    scopes = "offline_access"
    state = b64(random.randbytes(9))
    verifier = b64(random.randbytes(87))
    challenge = b64(hashlib.sha256(verifier.encode("ascii")).digest())
    redirect_uri = f"http://localhost:8080"

    resp = httpx.get(issuer + "/.well-known/openid-configuration")
    resp.raise_for_status()
    config = resp.json()
    auth_endpoint = config["authorization_endpoint"]
    token_endpoint = config["token_endpoint"]
    done = threading.Condition()
    data = {}

    class Handler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            u = parse.urlparse(self.path)
            query = parse.parse_qs(u.query)
            resp = httpx.post(token_endpoint, data={
                "grant_type": "authorization_code",
                "code": query["code"][0],
                "code_verifier": verifier,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
            })
            if resp.status_code != 200:
                self.send_response(500)
                return
            data.update(resp.json())
            self.send_response(302)
            self.send_header("Location", "https://planet-sdk-for-python-v2.readthedocs.io/en/stable/cli/cli-guide/")
            self.end_headers()
            with done:
                done.notify()

    srv = server.HTTPServer(("", 8080), Handler)
    thread = threading.Thread(target=srv.serve_forever)
    thread.start()

    time.sleep(.5)

    webbrowser.open(auth_endpoint + "?" + parse.urlencode({
        "response_type": "code",
        "code_challenge_method": "S256",
        "scope": scopes,
        "code_challenge": challenge,
        "state": state,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }))

    with done:
        print("please login using your browser")
        done.wait(60)

    srv.shutdown()
    return data["access_token"], data["refresh_token"]
