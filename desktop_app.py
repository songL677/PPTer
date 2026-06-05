import atexit
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


APP_TITLE = "AI 学习助手"


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout: int = 30) -> bool:
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.4)
    return False


def _start_streamlit(port: int) -> subprocess.Popen:
    root = _project_root()
    app_path = root / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> int:
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"
    process = _start_streamlit(port)
    atexit.register(process.terminate)

    if not _wait_until_ready(url):
        process.terminate()
        print("应用启动失败，请在终端运行 streamlit run app.py 查看详细错误。")
        return 1

    try:
        import webview

        window = webview.create_window(APP_TITLE, url, width=1280, height=860)
        webview.start()
        process.terminate()
        return 0
    except Exception:
        webbrowser.open(url)
        print(f"{APP_TITLE} 已在浏览器中打开：{url}")
        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
