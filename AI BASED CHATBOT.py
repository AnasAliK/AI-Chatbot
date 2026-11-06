"""Run the Orbit chatbot locally with Python 3."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PAGE = Path(__file__).with_name("style.html")
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")


def get_reply(messages):
    payload = {
        "model": MODEL,
        "input": messages,
        "instructions": "You are Orbit, a helpful AI assistant. Use plain text for replies.",
        "store": False,
        "max_output_tokens": 2048,
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=45) as response:
        result = json.load(response)
    parts = []
    for item in result.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    parts.append(part["text"])
                elif part.get("type") == "refusal":
                    parts.append(part["refusal"])
    return "\n".join(parts).strip()


def valid_messages(messages):
    return (
        isinstance(messages, list)
        and 1 <= len(messages) <= 21
        and all(
            isinstance(message, dict)
            and set(message) == {"role", "content"}
            and message["role"] == ("user" if index % 2 == 0 else "assistant")
            and isinstance(message["content"], str)
            and 0 < len(message["content"]) <= 20000
            for index, message in enumerate(messages)
        )
        and messages[-1]["role"] == "user"
    )


class ChatHandler(BaseHTTPRequestHandler):
    def send_content(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, data):
        self.send_content(status, json.dumps(data).encode(), "application/json")

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/style.html"):
            self.send_content(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/status":
            self.send_json(200, {"live": bool(API_KEY)})
        else:
            self.send_error(404)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/chat":
            self.send_error(404)
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Expected JSON."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 512000:
                raise ValueError
            messages = json.loads(self.rfile.read(length))
            if not valid_messages(messages):
                raise ValueError
        except (ValueError, UnicodeError):
            self.send_json(400, {"error": "Invalid conversation."})
            return
        if not API_KEY:
            self.send_json(503, {"error": "Set OPENAI_API_KEY to enable live replies."})
            return
        try:
            reply = get_reply(messages)
        except (URLError, TimeoutError, ValueError):
            reply = ""
        if reply:
            self.send_json(200, {"reply": reply})
        else:
            self.send_json(502, {"error": "The AI service returned no reply."})


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", 7860), ChatHandler) as server:
        print("Orbit is running at http://127.0.0.1:7860", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
