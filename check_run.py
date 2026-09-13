import subprocess, sys, time

proc = subprocess.Popen(
    [sys.executable, "main.py"],
    cwd=".",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

try:
    time.sleep(35)
    if proc.poll() is None:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate(timeout=8)
    else:
        out, err = proc.communicate(timeout=8)

    print("RC:", proc.returncode)
    print("=== STDOUT ===")
    print(out if out else "(no output)")
    print("=== STDERR ===")
    print(err if err else "(no output)")
except Exception as e:
    print("CHECK ERROR:", e)
    try:
        proc.kill()
        out, err = proc.communicate(timeout=8)
        print("OUT:", out)
        print("ERR:", err)
    except Exception:
        pass
