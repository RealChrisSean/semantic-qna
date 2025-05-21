"""Simplified script to start the development server.

The script launches ``uvicorn`` with hot reload enabled and displays a small
progress bar while waiting for the server's ``/health`` endpoint to return a
successful response. It mirrors the behaviour of :mod:`run_with_bar` but with a
minimal log output.
"""

import shutil
import sys
from server_utils import start_server_with_progress

def main():
    """Run the dev server and wait for it to become available."""
    proc, _ = start_server_with_progress()
    
    # Tail Uvicorn logs so you still see reload messages
    try:
        shutil.copyfileobj(proc.stdout, sys.stdout)
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
