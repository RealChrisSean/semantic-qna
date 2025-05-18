"""Utility for launching the development server with a progress bar.

This script starts the FastAPI application using ``uvicorn`` and displays a
progress bar that updates until the server's health check endpoint responds
successfully. It is primarily intended for use while developing so that you get
immediate feedback about when the server is ready to accept requests.
"""

import subprocess
import time
import requests
import shutil
import sys
from rich.progress import Progress, BarColumn, TimeElapsedColumn

PORT = 8000
CMD  = ["uvicorn", "server:app", "--reload", "--host", "0.0.0.0", "--port", str(PORT)]

def server_ready():
    """Check whether the development server has started successfully."""

    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=0.1)
        return r.status_code == 200
    except requests.RequestException:
        return False

def main():
    """Start the dev server and display readiness progress."""

    start = time.perf_counter()
    proc  = subprocess.Popen(
        CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,          # decode bytes -> str so shutil.copyfileobj works
        bufsize=1,          # line‑buffered for real‑time logs
    )

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(bar_width=40, style="green"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        t = progress.add_task("Booting server…", total=None)
        while not server_ready():
            time.sleep(0.2)

        # fetch the actual status code for the final message
        status = requests.get(f"http://127.0.0.1:{PORT}/health").status_code
        progress.update(t, completed=100, description="Server ready")

    elapsed = time.perf_counter() - start
    print(f"✅  /health responded {status} in {elapsed:.2f}s (http://localhost:{PORT})")

    # Tail Uvicorn logs so you still see reload messages
    try:
        shutil.copyfileobj(proc.stdout, sys.stdout)
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()