import os
import subprocess
import glob
from google import genai
from google.genai import types
from colorama import Fore, Style, init

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDFIvL9eQNzm1vIYXEtNCSLt9sVD-BjH98"
PROJECT_ROOT = "/root/workspace"
MODEL_ID = "gemini-2.0-flash" 

# Initialize
init(autoreset=True)
client = genai.Client(api_key=API_KEY)

# --- TOOLS ---
def run_command(command: str):
    """Executes a shell command."""
    print(f"{Fore.YELLOW}⚙️  Running: {command}{Style.RESET_ALL}")
    try:
        result = subprocess.run(
            command, shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return f"✅ SUCCESS:\n{output}"
        else:
            return f"❌ ERROR:\n{output}"
    except Exception as e:
        return f"❌ EXCEPTION: {str(e)}"

def read_file(filepath: str):
    """Reads a file."""
    try:
        full_path = os.path.join(PROJECT_ROOT, filepath)
        with open(full_path, 'r') as f:
            return f"📄 CONTENT of {filepath}:\n{f.read()}"
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

def write_file(filepath: str, content: str):
    """Writes content to a file."""
    try:
        full_path = os.path.join(PROJECT_ROOT, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"✅ Successfully wrote to {filepath}"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"

# --- SYSTEM PROMPT ---
sys_instruct = """
You are the 'Gemini Operator', a DevOps AI.
You have tools to RUN commands, READ files, and WRITE files.
Always check if a file exists before editing.
Be concise.
"""

def chat_loop():
    print(f"{Fore.GREEN}🤖 Gemini Operator (New SDK) Ready.{Style.RESET_ALL}")
    
    chat = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            tools=[run_command, read_file, write_file],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )
    )

    while True:
        try:
            user_input = input(f"\n{Fore.BLUE}You: {Style.RESET_ALL}")
            if user_input.lower() in ['exit', 'quit']: break
            
            print(f"{Fore.CYAN}Thinking...{Style.RESET_ALL}")
            response = chat.send_message(user_input)
            print(f"\n{Fore.GREEN}Gemini:{Style.RESET_ALL} {response.text}")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    chat_loop()
