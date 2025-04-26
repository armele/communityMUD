import socket
import subprocess
import sys

def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

if not is_port_in_use("127.0.0.1", 8000):
    print("LLM service not running. Starting it now...")
    subprocess.Popen([
        sys.executable, "-m", "uvicorn", "dynquest.service.llm_service:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ])
else:
    print("LLM service already running.")
