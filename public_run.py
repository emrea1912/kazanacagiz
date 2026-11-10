import os
import sys
import time
import re
import subprocess
import threading
import webbrowser

CLOUDFLARED_PATH = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"

def start_backend():
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="warning")

def monitor_tunnel(proc):
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    public_url = None

    for line in iter(proc.stderr.readline, ""):
        if not line:
            break
        print(line, end="")
        match = url_pattern.search(line)
        if match and not public_url:
            public_url = match.group(0)
            print("\n" + "=" * 70)
            print("🎉 TEBRİKLER! SİTENİZ TÜM DÜNYAYA VE HERKESE AÇILDI:")
            print(f"👉 CANLI WEB ADRESİ: {public_url}")
            print("📱 Bu linki telefonundan, tabletinden veya arkadaşlarına göndererek")
            print("   hemen fotoğraf çekip test edebilirsin!")
            print("=" * 70 + "\n")
            try:
                webbrowser.open(public_url)
            except Exception:
                pass

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Kazanacağız - Herkese Açık Canlı Yayın Başlatılıyor...")
    print("=" * 70)

    # 1. Start FastAPI server in background thread
    server_thread = threading.Thread(target=start_backend, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    # 2. Check Cloudflared executable
    cf_bin = CLOUDFLARED_PATH if os.path.exists(CLOUDFLARED_PATH) else "cloudflared"

    try:
        proc = subprocess.Popen(
            [cf_bin, "tunnel", "--url", "http://127.0.0.1:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        monitor_tunnel(proc)
        proc.wait()
    except KeyboardInterrupt:
        print("\nCanlı yayın durduruldu.")
    except Exception as e:
        print(f"Hata: {e}")
        print("Yerel modda devam ediliyor: http://127.0.0.1:8000")
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except:
            pass
        server_thread.join()
