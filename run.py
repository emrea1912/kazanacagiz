import os
import sys
import webbrowser
import uvicorn

if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print("=" * 60)
    print("🚀 Kazanacağız - Akıllı Ders & Soru Takip Sistemi Başlatılıyor")
    print(f"🌐 Tarayıcıdan erişmek için: {url}")
    print("📱 Mobilden/Tabletten erişmek için aynı Wi-Fi ağındaki yerel IP'nizi kullanabilirsiniz.")
    print("=" * 60)

    # Automatically open default web browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
