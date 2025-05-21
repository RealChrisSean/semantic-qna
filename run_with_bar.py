"""Utility for launching the development server with a progress bar.

This script starts the FastAPI application using ``uvicorn`` and displays a
progress bar that updates until the server's health check endpoint responds
successfully. It is primarily intended for use while developing so that you get
immediate feedback about when the server is ready to accept requests.
"""

import shutil
import sys
from server_utils import start_server_with_progress

def main():
    """Start the dev server and display readiness progress."""
    proc, _ = start_server_with_progress(display_full_status=True)
    
    # Tail Uvicorn logs so you still see reload messages
    try:
        shutil.copyfileobj(proc.stdout, sys.stdout)
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
