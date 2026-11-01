import os
import sys

# Force UTF-8 on Windows stdout/stderr
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure current directory and backend/ are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print(">> Launching ShopMind RAG Engine & Web Interface")
    print(">> Local URL: http://localhost:8000")
    print(">> API Documentation: http://localhost:8000/docs")
    print("=" * 65)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
