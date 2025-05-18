"""Simplified script to start the development server.

The script launches ``uvicorn`` with hot reload enabled and displays a small
progress bar while waiting for the server's ``/health`` endpoint to return a
successful response. It mirrors the behaviour of :mod:`run_with_bar` but with a
minimal log output.
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
    """Return ``True`` once the local server responds successfully."""

    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=0.1)
        return r.status_code == 200
    except requests.RequestException:
        return False

def main():
    """Run the dev server and wait for it to become available."""

    start = time.perf_counter()
    proc  = subprocess.Popen(CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(bar_width=40, style="green"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        t = progress.add_task("Booting server…", total=None)
        while not server_ready():
            time.sleep(0.2)
        progress.update(t, completed=100)

    elapsed = time.perf_counter() - start
    print(f"✅  Server ready in {elapsed:.2f}s (http://localhost:{PORT})")

    # Tail Uvicorn logs so you still see reload messages
    try:
        shutil.copyfileobj(proc.stdout, sys.stdout)
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()