"""
Max Assistant - Main Entry Point
Launches the Flask server and opens the UI window.
"""
import sys
import os
import threading
import time
import subprocess
import webbrowser

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

from config import HOST, PORT, GROQ_API_KEY, ASSISTANT_NAME


def print_banner():
    """Print the Max startup banner."""
    try:
        banner = f"""
\033[96m
    ╔══════════════════════════════════════════════╗
    ║                                              ║
    ║       ███╗   ███╗ █████╗ ██╗  ██╗            ║
    ║       ████╗ ████║██╔══██╗╚██╗██╔╝            ║
    ║       ██╔████╔██║███████║ ╚███╔╝             ║
    ║       ██║╚██╔╝██║██╔══██║ ██╔██╗             ║
    ║       ██║ ╚═╝ ██║██║  ██║██╔╝ ██╗            ║
    ║       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝            ║
    ║                                              ║
    ║       AI Personal Assistant v1.0             ║
    ║       ─────────────────────────              ║
    ║       Status: \033[92mONLINE\033[96m                          ║
    ║       Server: http://{HOST}:{PORT}            ║
    ║                                              ║
    ╚══════════════════════════════════════════════╝
\033[0m"""
        print(banner)
    except Exception:
        print(f"\n================================================")
        print(f"             MAX PERSONAL ASSISTANT            ")
        print(f"================================================")
        print(f"  Status: ONLINE")
        print(f"  Server: http://{HOST}:{PORT}")
        print(f"================================================\n")


def check_api_key():
    """Check if the API key is configured."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        try:
            print("\033[93m")
            print("  [!] Notice: Groq API key not set in .env")
            print("  ----------------------------------------")
            print("  * System app controls & commands work offline!")
            print("  * To enable full conversational AI, add your free key at:")
            print("    https://console.groq.com (free, instant signup)")
            print("  * You can also paste it in the Max popup Settings!")
            print("\033[0m")
        except Exception:
            print("  [!] Notice: Groq API key not configured yet.")
        return False
    return True


def open_ui():
    """Open the UI in the best available window mode."""
    url = f"http://{HOST}:{PORT}"
    time.sleep(1.5)  # Wait for server to start

    # Try Edge in app mode first (looks like a native popup)
    try:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if not os.path.exists(edge_path):
            edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

        if os.path.exists(edge_path):
            subprocess.Popen([
                edge_path,
                f'--app={url}',
                '--window-size=440,720',
                '--window-position=100,100',
                '--disable-extensions',
                '--disable-infobars'
            ])
            print(f"\033[92m  [+] Max UI launched in Edge app mode\033[0m")
            return
    except Exception:
        pass

    # Try Chrome in app mode
    try:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                subprocess.Popen([
                    chrome_path,
                    f'--app={url}',
                    '--window-size=440,720',
                    '--window-position=100,100'
                ])
                print(f"\033[92m  [+] Max UI launched in Chrome app mode\033[0m")
                return
    except Exception:
        pass

    # Fallback: open in default browser
    webbrowser.open(url)
    print(f"\033[92m  [+] Max UI opened in default browser\033[0m")


def start_server():
    """Start the Flask server."""
    from server import app
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def main():
    """Main entry point."""
    print_banner()
    check_api_key()

    print(f"\033[96m  Starting {ASSISTANT_NAME}...\033[0m")
    print(f"\033[90m  Press Ctrl+C to stop\033[0m\n")

    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Open UI
    open_ui()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\033[96m  {ASSISTANT_NAME} shutting down. Goodbye!\033[0m\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
