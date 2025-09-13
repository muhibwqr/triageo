import time
from pathlib import Path
from slack_sdk import WebClient
from dotenv import load_dotenv
import os

from triage import parse_log, baseline_severity, summarize
from llm import triage_with_llm
from blockkit import triage_blocks as demo_blocks
from rag import search, build_index

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL = "#security-alerts"  # change to your Slack channel
LOG_FILE = "samples/auth_burst.log"  # path to the log file you want to tail

client = WebClient(token=SLACK_TOKEN)

def tail_log(file_path):
    """Generator that yields new lines as they are added to the file."""
    with open(file_path, "r") as f:
        f.seek(0, 2)  # move to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield line.strip()

def process_line(line):
    build_index()
    parsed = parse_log(line)
    severity = baseline_severity(parsed)
    summary = summarize(parsed)
    evidence = [d["text"] for d in search(summary, k=3)]
    result = triage_with_llm(summary=summary, baseline=severity, evidence_snippets=evidence)
    return result

def send_to_slack(result):
    blocks = demo_blocks(result)  # or triage_blocks(result)
    client.chat_postMessage(channel=CHANNEL, blocks=blocks)

if __name__ == "__main__":
    print(f"Starting real-time log monitoring on {LOG_FILE}...")
    for log_line in tail_log(LOG_FILE):
        print(f"Processing line: {log_line}")
        triage_result = process_line(log_line)
        send_to_slack(triage_result)
        print("✅ Sent alert to Slack!")