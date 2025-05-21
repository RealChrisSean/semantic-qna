"""
Shared utilities for server startup scripts.
"""

import requests
import subprocess
import time
from rich.progress import Progress, BarColumn, TimeElapsedColumn

def server_ready(port):
    """Return ``True`` once the local server responds successfully."""
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=0.1)
        return r.status_code == 200
    except requests.RequestException:
        return False

def create_uvicorn_command(port=8000):
    """Create the uvicorn command with standard parameters."""
    return ["uvicorn", "server:app", "--reload", "--host", "0.0.0.0", "--port", str(port)]

def start_server_with_progress(port=8000, display_full_status=False):
    """
    Start the uvicorn server and display a progress bar until it's ready.
    
    Args:
        port: The port to run the server on
        display_full_status: Whether to display full status info at completion
    
    Returns:
        The server process and elapsed time
    """
    cmd = create_uvicorn_command(port)
    start = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(bar_width=40, style="green"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        t = progress.add_task("Booting server…", total=None)
        while not server_ready(port):
            time.sleep(0.2)
        progress.update(t, completed=100, description="Server ready")
    
    elapsed = time.perf_counter() - start
    
    if display_full_status:
        status = requests.get(f"http://127.0.0.1:{port}/health").status_code
        print(f"✅  /health responded {status} in {elapsed:.2f}s (http://localhost:{port})")
    else:
        print(f"✅  Server ready in {elapsed:.2f}s (http://localhost:{port})")
    
    return proc, elapsed
