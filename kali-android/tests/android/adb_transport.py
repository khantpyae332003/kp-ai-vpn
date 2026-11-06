"""ADB subprocess transport; mutation callers must never be retried implicitly."""
import subprocess

def execute(command, *, timeout, read_only=False, on_retry=None):
    attempts=3 if read_only else 1
    for attempt in range(attempts):
        try:
            return subprocess.run(command,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired:
            if attempt+1==attempts:raise
            if on_retry:on_retry(attempt+1)
