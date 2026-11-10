# Kazanacağız - Akıllı Ders & Soru Takip Sistemi 🚀

> **Öğrenciler için Yapay Zekâ Destekli, Aralıklı Tekrar (Spaced Repetition) ve Topluluk Soru Havuzu Platformu**

---

## 📌 Öne Çıkan Özellikler

1. **Evrensel Erişim (Mobil, Tablet & Masaüstü Web):**
   * **PC / Masaüstü:** Ekran görüntüsü alındığında doğrudan **`Ctrl + V` (Kopyala-Yapıştır)**, sürükle-bırak veya dosya yükleme.
   * **Mobil / Tablet:** Cihaz kamerasından doğrudan çekim veya galeriden seçim (`capture="environment"`).
   * **PWA Desteği:** İster tarayıcıdan açılır, ister mobil ana ekrana uygulama gibi eklenir.

2. **Zorunlu Doğru Cevap Doğrulaması:**
   * Soru kaydedilmeden önce doğru cevabın (A, B, C, D veya E) girilmesi **zorunludur**.
   * Doğru cevap seçilmeden kaydet butonuna basılırsa sistem uyarı verir ve kaydı engeller.

3. **Aralıklı Tekrar (Spaced Repetition) Algoritması:**
   * Yüklenen soru ilk olarak **2 gün sonra** kullanıcının tekrar listesine düşer.
   * **Cevap Önceden Gösterilmez:** Soru çözülürken doğru cevap asla önden gösterilmez.
   * Öğrenci şıkkı işaretleyip "Cevabı Onayla" dediğinde:
     * **Doğru ise:** Kocaman, kalın yeşil **DOĞRU! 🎉** geri bildirimi verilir ve soru **+7 gün sonraya (1 hafta sonra)** ertelenir.
     * **Yanlış ise:** Kocaman, kalın kırmızı **YANLIŞ! ❌** geri bildirimi verilir, kullanıcının cevabı ile doğru cevap karşılaştırılır ve soru **ERTESİ GÜN (1 gün sonra)** tekrar sorulur.
   * **3 Hafta Üst Üste Bilme (Ustalık):** Soru 3 hafta boyunca doğru bilinirse "Usta" statüsüne geçer ve sonraki ay yapay zekâ veya diğer kullanıcılardan gelen benzer pekiştirme soruları çalışma döngüsüne eklenir.

4. **Çift Görünüm (Dual-View):**
   * **Orijinal Fotoğraf:** Sorunun çekilen/yapıştırılan ham hali.
   * **Dijital Kart:** Yapay zekâ tarafından okunup tertemiz dijital test formatına dökülmüş hali (soru kökü + A, B, C, D, E seçenekleri).

5. **"Yapay Zekâya Danış" Butonu:**
   * Soru çözüldükten sonra açılır; tıklandığında yapay zekâ adım adım çözümü, sorunun temel mantığını, çeldiricileri ve sınav tüyolarını açıklar.

6. **Türkiye Saati (10:00 ve 15:00) Bildirim Sistemi:**
   * Sabah 10:00'da o gün vadesi gelen sorular için hatırlatma gider.
   * Saat 15:00'te henüz çözülmemiş sorular varsa ikinci bir hatırlatma gönderilir.
   * O gün çözülmezse sorular ertesi güne devreder.

7. **Sınav İzolasyonu & "Diğer" Sınav Ekleme:**
   * Hazır ÖSYM Listesi: YKS (TYT-AYT), KPSS (Lisans, Ön Lisans, Ortaöğretim), AGS, ALES, DGS, MSÜ, YDS, LGS vb.
   * **"Diğer" Seçeneği:** Kullanıcı listede olmayan bir sınav girdiğinde (örn. Kaymakamlık), **kullanıcı için anında aktifleşir** ve soru yüklemeye devam eder.
   * **Admin Onay Paneli:** Kullanıcıların eklediği yeni sınavlar adminin önüne düşer. Admin "Onayla" dediği an sistemdeki tüm kullanıcılara açılır.

8. **2. Mod: Topluluk Zor Sorular Havuzu:**
   * Başka öğrencilerin yanlış yaptığı soruları içerir.
   * Sadece kullanıcının aktif sınavına ait sorular listelenir; diğer sınavların sorularıyla kesinlikle karışmaz.

9. **Premium Hesap Sistemi:**
   * **Ücretsiz Hesap:** Günlük 5 soru yükleme limiti.
   * **Premium Hesap:** Sınırsız soru yükleme, Topluluk Havuzu modu, sınırsız yapay zekâ çözümü.

---

## 🛠️ Nasıl Çalıştırılır?

### 1. Herkese Açık Canlı İnternet Yayını (Telefondan / Dışarıdan Giriş İçin):
Telefonundan, tabletinden veya arkadaşlarının bilgisayarından doğrudan girmesini istiyorsan:
```bash
python public_run.py
```
*(veya **`canli_yayin.bat`** dosyasına çift tıklayın).*
Sistem size anında `https://xxxx.trycloudflare.com` şeklinde dünya genelinde geçerli, güvenli (SSL'li) bir canlı link üretecek ve tarayıcınızda açacaktır!

### 2. Sadece Kendi Bilgisayarınızda (Yerel Mod):
```bash
python run.py
```
*(veya **`start.bat`** dosyasına çift tıklayın -> `http://127.0.0.1:8000`).*

---

## 🔑 Hesaplar ve Premium Lisans Anahtarları

* **Giriş Bilgileri:**
  * Öğrenci Hesabı: `ogrenci` / `ogrenci123`
  * Yönetici (Admin) Hesabı: `admin` / `admin123`
  * Veya açılış ekranından anında **Yeni Kayıt Ol**abilirsiniz!

* **Test İçin Geçerli Premium Lisans Anahtarları:**
  * `KAZAN-PRO-2026` (30 Günlük)
  * `DERECE-VIP-30` (30 Günlük)
  * `YILLIK-SAMPIYON-365` (1 Yıllık)
  * *(Admin panelinden istediğiniz kadar yeni lisans anahtarı da üretebilirsiniz).*
