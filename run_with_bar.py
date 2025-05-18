# run_with_bar.py
import subprocess, time, requests, shutil, sys
from rich.progress import Progress, BarColumn, TimeElapsedColumn

PORT = 8000
CMD  = ["uvicorn", "server:app", "--reload", "--host", "0.0.0.0", "--port", str(PORT)]

def server_ready():
    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=0.1)
        return r.status_code == 200
    except requests.RequestException:
        return False

def main():
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