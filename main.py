import threading, os
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from app import app as bolt_app
import uvicorn

load_dotenv()

def run_slack():
    SocketModeHandler(bolt_app, os.getenv("SLACK_APP_TOKEN")).start()

def run_http():
    uvicorn.run("server:api", host="0.0.0.0", port=8080, reload=False)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_slack, daemon=True)
    t1.start()
    run_http()
