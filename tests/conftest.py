import os
import sys

# Make the repo root importable (so `from utils...` / `from tools...` work
# the same way they do when running `uvicorn main:app` from the repo root).
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
