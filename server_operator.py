import os
import subprocess
import sys
import datetime
import getpass
from google import genai
from google.genai import types
from colorama import Fore, Style, init

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = "/root/workspace"
MODEL_ID = "gemini-2.0-flash" 

init(autoreset=True)

# --- SAFE CLIENT INIT ---
if not API_KEY:
    print(f"{Fore.RED}❌ Error: API Key is missing. Please export GEMINI_API_KEY.{Style.RESET_ALL}")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# --- TOOLS ---
def run_command(command: str):
    print(f"{Fore.YELLOW}⚙️  Running: {command}{Style.RESET_ALL}")
    try:
        result = subprocess.run(
            command, shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60
        )
        return f"Output:\n{result.stdout + result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

def read_file(filepath: str):
    try:
        with open(os.path.join(PROJECT_ROOT, filepath), 'r') as f: return f.read()
    except Exception as e: return f"Error reading: {str(e)}"

def write_file(filepath: str, content: str):
    try:
        path = os.path.join(PROJECT_ROOT, filepath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f: f.write(content)
        return "Success"
    except Exception as e: return f"Error writing: {str(e)}"

def log_task(task: str, status: str, details: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_details = details.replace("|", "-").replace("\n", " ")[:150] 
    entry = f"\n| {timestamp} | {task} | {status} | {clean_details} |"
    try:
        with open(os.path.join(PROJECT_ROOT, "AGENT_LOG.md"), 'a') as f: f.write(entry)
        return "Logged."
    except Exception as e: return f"Log failed: {e}"

def update_status(component: str, status: str):
    entry = f"- **{component}:** {status} (Updated: {datetime.datetime.now().strftime('%H:%M')})\n"
    try:
        with open(os.path.join(PROJECT_ROOT, "PROJECT_STATUS.md"), 'a') as f: f.write(entry)
        return "Status Updated."
    except Exception as e: return f"Status update failed: {e}"

# --- SYSTEM PROMPT ---
sys_instruct = """
You are the 'Server Operator'. 
RULES:
1. You maintain the server. You DO NOT write feature code (leave that to Antigravity).
2. You MUST use `log_task` after every action.
3. If you fix a crash or change a port, use `update_status` so Antigravity knows.
4. Read 'AGENT_PROTOCOLS.md' before starting complex tasks.
"""

def chat_loop():
    print(f"{Fore.GREEN}🤖 Operator Ready. (Logs & Status Sync Active){Style.RESET_ALL}")
    chat = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            tools=[run_command, read_file, write_file, log_task, update_status],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )
    )
    while True:
        try:
            user = input(f"\n{Fore.BLUE}You: {Style.RESET_ALL}")
            if user.lower() in ['exit', 'quit']: break
            print(f"{Fore.CYAN}Thinking...{Style.RESET_ALL}")
            print(f"\n{Fore.GREEN}Gemini:{Style.RESET_ALL} {chat.send_message(user).text}")
        except Exception as e: print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    chat_loop()
