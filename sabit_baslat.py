import os
import sys
import time
import subprocess
import threading
import webbrowser
import urllib.request

NODE_DIR = r"C:\Program Files\nodejs"
os.environ["PATH"] = f"{NODE_DIR};" + os.environ.get("PATH", "")

def get_public_ip():
    try:
        req = urllib.request.Request("https://ipv4.icanhazip.com", headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return "212.252.17.75"

def start_backend():
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    ip = get_public_ip()
    subdomain = "kazanacagiz-soru"
    fixed_url = f"https://{subdomain}.loca.lt"

    print("=" * 70)
    print("🚀 Kazanacağız - Sabit ve Kalıcı Alan Adı Başlatılıyor...")
    print("=" * 70)
    print(f"\n👉 SABİT SİTE ADRESİNİZ: {fixed_url}")
    print(f"🔑 İLK GİRİŞ DOĞRULAMA ŞİFRENİZ (IP): {ip}")
    print("   (İlk açılışta güvenlik sayfası çıkarsa bu IP'yi girip 'Click to Submit'e basın)")
    print("=" * 70 + "\n")

    # Start backend
    server_thread = threading.Thread(target=start_backend, daemon=True)
    server_thread.start()
    time.sleep(2)

    # Open in browser
    try:
        webbrowser.open(fixed_url)
    except:
        pass

    # Start localtunnel
    npx_cmd = os.path.join(NODE_DIR, "npx.cmd") if os.path.exists(os.path.join(NODE_DIR, "npx.cmd")) else "npx"
    try:
        proc = subprocess.Popen([npx_cmd, "localtunnel", "--port", "8000", "--subdomain", subdomain])
        proc.wait()
    except KeyboardInterrupt:
        print("\nProgram kapatıldı.")
