import os
import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import get_connection, init_db
from backend.services.ai_service import (
    analyze_question_image,
    explain_solution_with_ai,
    generate_similar_practice_question
)
from backend.services.scheduler_service import (
    get_due_questions,
    record_answer_and_reschedule,
    check_and_create_daily_reminders
)

# Initialize Database
init_db()

app = FastAPI(title="Kazanacağız - Akıllı Ders & Soru Takip Sistemi", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Session / Auth Helper
def get_current_user(
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
    elif x_session_token:
        token = x_session_token.strip()

    conn = get_connection()
    cursor = conn.cursor()

    if token:
        cursor.execute("SELECT * FROM users WHERE session_token = ?", (token,))
        user = cursor.fetchone()
        if user:
            conn.close()
            return dict(user)

    if x_user_id:
        cursor.execute("SELECT * FROM users WHERE id = ?", (int(x_user_id),))
        user = cursor.fetchone()
        if user:
            conn.close()
            return dict(user)

    conn.close()
    raise HTTPException(status_code=401, detail="Lütfen giriş yapınız.")

# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    selected_exam_id: Optional[int] = 1

class CustomExamRequest(BaseModel):
    name: str

class AnswerSubmission(BaseModel):
    question_id: int
    given_answer: str

class ExplainRequest(BaseModel):
    question_id: int

class UpdateExamRequest(BaseModel):
    exam_id: int

class RedeemKeyRequest(BaseModel):
    key_code: str

class PaymentSimulateRequest(BaseModel):
    plan: str # 'monthly' or 'yearly'
    card_number: str
    card_holder: str
    expiry: str
    cvv: str

class GenerateKeyRequest(BaseModel):
    duration_days: Optional[int] = 30

# --- API Endpoints ---

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.api_route("/healthz", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (req.username.strip(), req.password.strip()))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Hatalı kullanıcı adı veya şifre!")
    
    token = f"tok_{uuid.uuid4().hex}"
    cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (token, user["id"]))
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
    updated_user = cursor.fetchone()
    conn.close()
    
    user_dict = dict(updated_user)
    user_dict.pop("password_hash", None)
    return {"status": "ok", "token": token, "user": user_dict}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    username = req.username.strip()
    password = req.password.strip()
    if len(username) < 3 or len(password) < 4:
        raise HTTPException(status_code=400, detail="Kullanıcı adı en az 3, şifre en az 4 karakter olmalıdır.")

    conn = get_connection()
    cursor = conn.cursor()
    token = f"tok_{uuid.uuid4().hex}"
    try:
        cursor.execute("""
        INSERT INTO users (username, password_hash, session_token, role, is_premium, selected_exam_id)
        VALUES (?, ?, ?, 'user', 0, ?)
        """, (username, password, token, req.selected_exam_id or 1))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        user_dict = dict(user)
        user_dict.pop("password_hash", None)
        return {"status": "ok", "token": token, "user": user_dict}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış!")

@app.post("/api/auth/logout")
def logout(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET session_token = NULL WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Çıkış yapıldı"}

@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM exams WHERE id = ?", (user.get("selected_exam_id"),))
    exam_row = cursor.fetchone()
    conn.close()
    user_copy = dict(user)
    user_copy.pop("password_hash", None)
    user_copy["selected_exam_name"] = exam_row["name"] if exam_row else "Belirtilmemiş"
    return user_copy

# --- REAL PREMIUM ACTIVATION: LICENSE KEY OR SIMULATED PAYMENT ---

@app.post("/api/premium/redeem-key")
def redeem_license_key(req: RedeemKeyRequest, user: dict = Depends(get_current_user)):
    key = req.key_code.strip().upper()
    if not key:
        raise HTTPException(status_code=400, detail="Lütfen bir lisans anahtarı giriniz.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM license_keys WHERE key_code = ?", (key,))
    key_row = cursor.fetchone()

    if not key_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Geçersiz lisans anahtarı!")
    
    if key_row["is_used"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Bu lisans anahtarı daha önce kullanılmış!")

    days = key_row["duration_days"] or 30
    until_date = (date.today() + timedelta(days=days)).isoformat()

    # Mark key as used
    cursor.execute("""
    UPDATE license_keys 
    SET is_used = 1, used_by_user_id = ? 
    WHERE id = ?
    """, (user["id"], key_row["id"]))

    # Upgrade user to Premium
    cursor.execute("""
    UPDATE users 
    SET is_premium = 1, premium_until = ? 
    WHERE id = ?
    """, (until_date, user["id"]))

    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "message": f"Tebrikler! 🎉 Lisans anahtarı başarıyla aktif edildi. Premium üyeliğiniz {until_date} tarihine kadar geçerlidir.",
        "premium_until": until_date
    }

@app.post("/api/premium/simulate-payment")
def simulate_payment(req: PaymentSimulateRequest, user: dict = Depends(get_current_user)):
    card_clean = req.card_number.replace(" ", "").replace("-", "")
    if len(card_clean) < 15 or len(req.cvv) < 3:
        raise HTTPException(status_code=400, detail="Kart bilgileri geçersiz! Lütfen kontrol ediniz.")

    days = 365 if req.plan == "yearly" else 30
    until_date = (date.today() + timedelta(days=days)).isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET is_premium = 1, premium_until = ? 
    WHERE id = ?
    """, (until_date, user["id"]))
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "message": f"Ödemeniz başarıyla onaylandı! {days} günlük Premium üyeliğiniz aktif edildi.",
        "premium_until": until_date
    }

@app.get("/api/admin/license-keys")
def get_admin_license_keys(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli!")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT lk.*, u.username as used_by_username
    FROM license_keys lk
    LEFT JOIN users u ON lk.used_by_user_id = u.id
    ORDER BY lk.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/admin/generate-key")
def generate_license_key(req: GenerateKeyRequest, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli!")
    key_code = f"KZ-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO license_keys (key_code, is_used, duration_days)
    VALUES (?, 0, ?)
    """, (key_code, req.duration_days or 30))
    conn.commit()
    conn.close()
    return {"status": "ok", "key_code": key_code, "duration_days": req.duration_days or 30}

@app.post("/api/auth/update-exam")
def update_user_exam(req: UpdateExamRequest, user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET selected_exam_id = ? WHERE id = ?", (req.exam_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "ok", "selected_exam_id": req.exam_id}

# --- Exams ---
@app.get("/api/exams")
def get_exams(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    # List approved exams + unapproved ones created by this user
    cursor.execute("""
    SELECT * FROM exams 
    WHERE is_approved = 1 OR created_by_user_id = ?
    ORDER BY is_approved DESC, name ASC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/exams/custom")
def add_custom_exam(req: CustomExamRequest, user: dict = Depends(get_current_user)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Sınav adı boş olamaz!")
    
    code = "CUSTOM_" + uuid.uuid4().hex[:8].upper()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO exams (name, code, is_approved, created_by_user_id)
        VALUES (?, ?, 0, ?)
        """, (name, code, user["id"]))
        exam_id = cursor.lastrowid
        # Automatically set as user's active exam so they can immediately use it
        cursor.execute("UPDATE users SET selected_exam_id = ? WHERE id = ?", (exam_id, user["id"]))
        conn.commit()
        conn.close()
        return {
            "status": "ok", 
            "exam": {"id": exam_id, "name": name, "code": code, "is_approved": False},
            "message": "Sınavınız eklendi ve hemen seçildi. Yönetici onayından sonra tüm kullanıcıların listesine eklenecektir."
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail="Sınav eklenirken bir hata oluştu.")

# --- Admin Endpoints ---
@app.get("/api/admin/pending-exams")
def get_pending_exams(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli!")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT e.*, u.username as creator_username
    FROM exams e
    LEFT JOIN users u ON e.created_by_user_id = u.id
    WHERE e.is_approved = 0
    ORDER BY e.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/admin/approve-exam/{exam_id}")
def approve_exam(exam_id: int, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli!")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE exams SET is_approved = 1 WHERE id = ?", (exam_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Sınav onaylandı ve genele açıldı."}

@app.get("/api/admin/stats")
def get_admin_stats(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yönetici yetkisi gerekli!")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()["total_users"]
    cursor.execute("SELECT COUNT(*) as total_questions FROM questions")
    total_questions = cursor.fetchone()["total_questions"]
    cursor.execute("SELECT COUNT(*) as pending_exams FROM exams WHERE is_approved = 0")
    pending_exams = cursor.fetchone()["pending_exams"]
    conn.close()
    return {
        "total_users": total_users,
        "total_questions": total_questions,
        "pending_exams": pending_exams
    }

# --- Questions Management ---
@app.get("/api/questions/due")
def get_user_due_questions(user: dict = Depends(get_current_user)):
    """
    Returns questions due today. Correct answer is deliberately OMITTED 
    so the user cannot cheat before answering.
    """
    due_list = get_due_questions(user["id"])
    sanitized = []
    for q in due_list:
        item = dict(q)
        item.pop("correct_answer", None) # Hide correct answer!
        sanitized.append(item)
    return sanitized

@app.get("/api/questions/all")
def get_all_user_questions(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.*, e.name as exam_name
    FROM questions q
    JOIN exams e ON q.exam_id = e.id
    WHERE q.user_id = ?
    ORDER BY q.created_at DESC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/questions/upload")
async def upload_question(
    image: UploadFile = File(...),
    correct_answer: str = Form(...),
    subject: Optional[str] = Form("Genel"),
    topic: Optional[str] = Form("Genel"),
    user: dict = Depends(get_current_user)
):
    # Mandatory Correct Answer Validation
    ans = (correct_answer or "").strip().upper()
    if ans not in ["A", "B", "C", "D", "E"]:
        raise HTTPException(
            status_code=400, 
            detail="HATA: Lütfen sorunun doğru cevabını (A, B, C, D veya E) giriniz! Doğru cevapsız soru kaydedilemez."
        )

    # Free User Daily Upload Limit (Max 5 per day)
    today_str = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*) as count_today
    FROM questions
    WHERE user_id = ? AND date(created_at) = ?
    """, (user["id"], today_str))
    upload_count = cursor.fetchone()["count_today"]

    if not user.get("is_premium") and upload_count >= 5:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Günlük 5 soru yükleme limitinize ulaştınız! Sınırsız yükleme ve topluluk havuzu için Premium'a geçebilirsiniz."
        )

    # Save Image to disk
    ext = os.path.splitext(image.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    image_url = f"/uploads/{filename}"

    # AI Processing for Digital Card extraction
    ai_result = analyze_question_image(
        image_bytes=content,
        file_name=filename,
        custom_subject=subject,
        custom_topic=topic
    )

    # Spaced Repetition Initial Schedule: First encounter in 2 days
    next_review = (date.today() + timedelta(days=2)).isoformat()
    exam_id = user.get("selected_exam_id", 1)

    cursor.execute("""
    INSERT INTO questions (
        user_id, exam_id, subject, topic, image_url,
        digital_question_text, option_a, option_b, option_c, option_d, option_e,
        correct_answer, next_review_date, consecutive_correct, total_reviews,
        mastered, is_public_pool, source_type
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 1, 'user_upload')
    """, (
        user["id"],
        exam_id,
        ai_result["subject"],
        ai_result["topic"],
        image_url,
        ai_result["question_text"],
        ai_result["option_a"],
        ai_result["option_b"],
        ai_result["option_c"],
        ai_result["option_d"],
        ai_result["option_e"],
        ans,
        next_review
    ))
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "question_id": question_id,
        "message": f"Soru başarıyla kaydedildi! İlk tekrarın 2 gün sonra ({next_review}) önüne gelecektir.",
        "next_review_date": next_review
    }

@app.post("/api/questions/answer")
def submit_question_answer(sub: AnswerSubmission, user: dict = Depends(get_current_user)):
    result = record_answer_and_reschedule(
        question_id=sub.question_id,
        user_id=user["id"],
        given_answer=sub.given_answer
    )
    if not result:
        raise HTTPException(status_code=404, detail="Soru bulunamadı veya yetkiniz yok!")
    return result

@app.post("/api/questions/ai-explain")
def get_ai_explanation(req: ExplainRequest, user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (req.question_id,))
    q = cursor.fetchone()
    conn.close()
    if not q:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")

    options = {
        "A": q["option_a"] or "A",
        "B": q["option_b"] or "B",
        "C": q["option_c"] or "C",
        "D": q["option_d"] or "D",
        "E": q["option_e"] or "E"
    }

    explanation = explain_solution_with_ai(
        question_text=q["digital_question_text"] or "Görseldeki soru",
        options=options,
        correct_answer=q["correct_answer"],
        subject=q["subject"] or "",
        topic=q["topic"] or ""
    )
    return {"explanation": explanation}

# --- Mode 2: Topluluk Soru Havuzu (Community Wrong Pool) ---
@app.get("/api/questions/community-pool")
def get_community_pool(user: dict = Depends(get_current_user)):
    """
    Fetches random questions that other users failed to solve, 
    FILTERED STRICTLY by the current user's active exam!
    """
    conn = get_connection()
    cursor = conn.cursor()
    active_exam_id = user.get("selected_exam_id", 1)

    # Questions where another user answered wrongly, matching active exam
    cursor.execute("""
    SELECT DISTINCT q.id, q.subject, q.topic, q.image_url, 
           q.digital_question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
           e.name as exam_name
    FROM questions q
    JOIN review_logs rl ON q.id = rl.question_id
    JOIN exams e ON q.exam_id = e.id
    WHERE q.exam_id = ? AND q.user_id != ? AND rl.is_correct = 0
    ORDER BY RANDOM()
    LIMIT 20
    """, (active_exam_id, user["id"]))
    rows = cursor.fetchall()
    
    # If not enough community wrong questions yet, offer other pool questions from same exam
    if not rows:
        cursor.execute("""
        SELECT q.id, q.subject, q.topic, q.image_url, 
               q.digital_question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
               e.name as exam_name
        FROM questions q
        JOIN exams e ON q.exam_id = e.id
        WHERE q.exam_id = ? AND q.user_id != ?
        ORDER BY RANDOM()
        LIMIT 20
        """, (active_exam_id, user["id"]))
        rows = cursor.fetchall()

    conn.close()
    return [dict(r) for r in rows]

# --- 3-Week Mastery Practice (Cross-User & AI Matching) ---
@app.get("/api/questions/mastered-practice")
def get_mastered_practice(user: dict = Depends(get_current_user)):
    """
    For questions answered correctly 3 consecutive weeks, find cross-user 
    questions or AI questions in the same topic.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT subject, topic FROM questions 
    WHERE user_id = ? AND mastered = 1
    """, (user["id"],))
    mastered_topics = cursor.fetchall()
    
    results = []
    active_exam_id = user.get("selected_exam_id", 1)
    
    for row in mastered_topics:
        subj = row["subject"]
        top = row["topic"]
        # Find from other users
        cursor.execute("""
        SELECT q.id, q.subject, q.topic, q.image_url, 
               q.digital_question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
               e.name as exam_name
        FROM questions q
        JOIN exams e ON q.exam_id = e.id
        WHERE q.exam_id = ? AND q.user_id != ? AND q.subject = ? AND q.topic = ?
        LIMIT 5
        """, (active_exam_id, user["id"], subj, top))
        peer_qs = cursor.fetchall()
        for pq in peer_qs:
            results.append(dict(pq))
            
    conn.close()
    return results

# --- Notifications / Schedule Sync ---
@app.get("/api/notifications")
def get_notifications(user: dict = Depends(get_current_user)):
    check_and_create_daily_reminders()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM reminders 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 20
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
