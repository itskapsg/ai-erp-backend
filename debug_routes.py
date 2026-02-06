
import sys
import os

# Add workspace to path
sys.path.append(os.getcwd())

from app.main import app

def list_routes():
    print("--- Detailed Route Dump ---")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)
        print(f"Path: {path} | Methods: {methods} | Name: {name}")

if __name__ == "__main__":
    list_routes()
