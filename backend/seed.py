import os
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def seed_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    # Create dummy SVG question images for offline testing
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    img1_path = os.path.join(uploads_dir, "sample_cografya.svg")
    with open(img1_path, "w", encoding="utf-8") as f:
        f.write('''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
  <rect width="600" height="400" fill="#f8fafc"/>
  <rect x="20" y="20" width="560" height="360" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <text x="50" y="70" font-family="sans-serif" font-size="20" font-weight="bold" fill="#1e293b">KPSS Coğrafya - Türkiye'nin Dağları</text>
  <text x="50" y="120" font-family="sans-serif" font-size="16" fill="#334155">Aşağıdaki dağlardan hangisi volkanik oluşumlu bir dağ DEĞİLDİR?</text>
  <text x="70" y="170" font-family="sans-serif" font-size="15" fill="#475569">A) Ağrı Dağı</text>
  <text x="70" y="210" font-family="sans-serif" font-size="15" fill="#475569">B) Erciyes Dağı</text>
  <text x="70" y="250" font-family="sans-serif" font-size="15" fill="#475569">C) Kaçkar Dağları</text>
  <text x="70" y="290" font-family="sans-serif" font-size="15" fill="#475569">D) Nemrut Dağı</text>
  <text x="70" y="330" font-family="sans-serif" font-size="15" fill="#475569">E) Süphan Dağı</text>
  <circle cx="280" cy="245" r="14" fill="none" stroke="#ef4444" stroke-width="3" opacity="0.6"/>
  <path d="M 50 140 Q 200 130 350 140" fill="none" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4" opacity="0.5"/>
</svg>''')

    img2_path = os.path.join(uploads_dir, "sample_matematik.svg")
    with open(img2_path, "w", encoding="utf-8") as f:
        f.write('''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
  <rect width="600" height="400" fill="#f8fafc"/>
  <rect x="20" y="20" width="560" height="360" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <text x="50" y="70" font-family="sans-serif" font-size="20" font-weight="bold" fill="#1e293b">YKS Matematik - Fonksiyonlar</text>
  <text x="50" y="120" font-family="sans-serif" font-size="16" fill="#334155">f(x) = 3x - 5 olduğuna göre, f(2x + 1) fonksiyonu nedir?</text>
  <text x="70" y="170" font-family="sans-serif" font-size="15" fill="#475569">A) 6x - 2</text>
  <text x="70" y="210" font-family="sans-serif" font-size="15" fill="#475569">B) 6x - 4</text>
  <text x="70" y="250" font-family="sans-serif" font-size="15" fill="#475569">C) 3x - 2</text>
  <text x="70" y="290" font-family="sans-serif" font-size="15" fill="#475569">D) 6x + 3</text>
  <text x="70" y="330" font-family="sans-serif" font-size="15" fill="#475569">E) 3x - 5</text>
</svg>''')

    # Seed or reset User 2 (Öğrenci) sample due question for KPSS Lisans (exam_id=2 or 1)
    cursor.execute("SELECT id FROM exams WHERE code = 'KPSS_LISANS'")
    kpss_id = cursor.fetchone()
    kpss_exam_id = kpss_id[0] if kpss_id else 2

    # Set user 2 active exam to KPSS Lisans
    cursor.execute("UPDATE users SET selected_exam_id = ? WHERE id = 2", (kpss_exam_id,))

    cursor.execute("""
    INSERT OR REPLACE INTO questions (
        id, user_id, exam_id, subject, topic, image_url,
        digital_question_text, option_a, option_b, option_c, option_d, option_e,
        correct_answer, next_review_date, consecutive_correct, total_reviews,
        mastered, is_public_pool, source_type
    ) VALUES (
        1, 2, ?, 'Coğrafya', "Türkiye'nin Dağları", '/uploads/sample_cografya.svg',
        'Aşağıdaki dağlardan hangisi volkanik oluşumlu bir dağ DEĞİLDİR?',
        'Ağrı Dağı', 'Erciyes Dağı', 'Kaçkar Dağları', 'Nemrut Dağı', 'Süphan Dağı',
        'C', ?, 0, 0, 0, 1, 'user_upload'
    )
    """, (kpss_exam_id, today_str))

    # Seed User 1 (Admin/Peer) community question for same exam with a wrong log
    cursor.execute("""
    INSERT OR IGNORE INTO questions (
        id, user_id, exam_id, subject, topic, image_url,
        digital_question_text, option_a, option_b, option_c, option_d, option_e,
        correct_answer, next_review_date, consecutive_correct, total_reviews,
        mastered, is_public_pool, source_type
    ) VALUES (
        2, 1, ?, 'Tarih', 'Kurtuluş Savaşı Muharebeler', '/uploads/sample_cografya.svg',
        'Kurtuluş Savaşı döneminde düzenli ordunun ilk askeri başarısı aşağıdakilerden hangisidir?',
        'I. İnönü Muharebesi', 'II. İnönü Muharebesi', 'Sakarya Meydan Muharebesi', 'Büyük Taarruz', 'Eskişehir-Kütahya Muharebeleri',
        'A', ?, 0, 1, 0, 1, 'user_upload'
    )
    """, (kpss_exam_id, yesterday_str))

    # Log user 1 failing this question so it appears in Community Wrong Questions
    cursor.execute("""
    INSERT OR IGNORE INTO review_logs (id, question_id, user_id, given_answer, is_correct)
    VALUES (1, 2, 1, 'C', 0)
    """)

    # Seed a custom exam pending admin approval to showcase the admin workflow
    cursor.execute("""
    INSERT OR IGNORE INTO exams (id, name, code, is_approved, created_by_user_id)
    VALUES (99, 'Kaymakamlık Adaylığı Sınavı', 'CUSTOM_KAYMAKAM', 0, 2)
    """)

    # Reset sample license key for repeated test runs
    cursor.execute("UPDATE license_keys SET is_used = 0, used_by_user_id = NULL WHERE key_code = 'KAZAN-PRO-2026'")
    cursor.execute("UPDATE users SET is_premium = 0 WHERE id = 2")

    conn.commit()
    conn.close()
    print("Sample data seeded successfully!")

if __name__ == "__main__":
    seed_sample_data()
