import os
import sqlite3
from datetime import datetime, date, timedelta
from backend.database import get_connection

def get_due_questions(user_id: int):
    """
    Returns questions that are due on or before today for the given user.
    """
    today_str = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.*, e.name as exam_name
    FROM questions q
    JOIN exams e ON q.exam_id = e.id
    WHERE q.user_id = ? AND q.next_review_date <= ?
    ORDER BY q.next_review_date ASC
    """, (user_id, today_str))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def check_and_create_daily_reminders():
    """
    Simulates checking current Turkey time (10:00 and 15:00) and generating reminder logs.
    Can be run via cron, background task or on-demand sync.
    """
    conn = get_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    now = datetime.now()
    current_hour = now.hour

    # Find all users with due questions today
    cursor.execute("""
    SELECT DISTINCT u.id, u.username, COUNT(q.id) as due_count
    FROM users u
    JOIN questions q ON u.id = q.user_id
    WHERE q.next_review_date <= ?
    GROUP BY u.id
    """, (today_str,))
    users_with_due = cursor.fetchall()

    for user in users_with_due:
        u_id = user["id"]
        due_count = user["due_count"]

        # 10:00 Morning Check
        if current_hour >= 10:
            cursor.execute("""
            SELECT id FROM reminders 
            WHERE user_id = ? AND reminder_date = ? AND reminder_type = 'morning_10'
            """, (u_id, today_str))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
                VALUES (?, 'morning_10', ?, ?)
                """, (u_id, today_str, f"Günaydın! Bugün tekrar etmen gereken {due_count} soru seni bekliyor."))

        # 15:00 Afternoon Check (if questions still remain)
        if current_hour >= 15:
            cursor.execute("""
            SELECT id FROM reminders 
            WHERE user_id = ? AND reminder_date = ? AND reminder_type = 'afternoon_15'
            """, (u_id, today_str))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
                VALUES (?, 'afternoon_15', ?, ?)
                """, (u_id, today_str, f"Hatırlatma: Bugün henüz çözmediğin {due_count} tekrar sorusu var. Hedefine bir adım daha yaklaş!"))

    conn.commit()
    conn.close()

def record_answer_and_reschedule(question_id: int, user_id: int, given_answer: str):
    """
    Processes the answer:
    - Compares given_answer with correct_answer (case insensitive)
    - If correct: +7 days, consecutive_correct + 1
    - If wrong: +1 day (tomorrow), consecutive_correct = 0
    - If consecutive_correct reaches 3: marks mastered = 1
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM questions WHERE id = ? AND user_id = ?", (question_id, user_id))
    q = cursor.fetchone()
    if not q:
        conn.close()
        return None

    correct_ans = q["correct_answer"].strip().upper()
    user_ans = given_answer.strip().upper()
    is_correct = (correct_ans == user_ans)
    
    today = date.today()
    current_consecutive = q["consecutive_correct"]

    if is_correct:
        new_consecutive = current_consecutive + 1
        next_date = today + timedelta(days=7) # +1 hafta sonra
        mastered = 1 if new_consecutive >= 3 else 0
    else:
        new_consecutive = 0
        next_date = today + timedelta(days=1) # Ertesi gün tekrar
        mastered = 0

    next_date_str = next_date.isoformat()

    cursor.execute("""
    UPDATE questions 
    SET next_review_date = ?, 
        consecutive_correct = ?, 
        total_reviews = total_reviews + 1,
        mastered = ?
    WHERE id = ?
    """, (next_date_str, new_consecutive, mastered, question_id))

    # Log the review attempt
    cursor.execute("""
    INSERT INTO review_logs (question_id, user_id, given_answer, is_correct)
    VALUES (?, ?, ?, ?)
    """, (question_id, user_id, user_ans, 1 if is_correct else 0))

    conn.commit()
    conn.close()

    return {
        "question_id": question_id,
        "is_correct": is_correct,
        "given_answer": user_ans,
        "correct_answer": correct_ans,
        "consecutive_correct": new_consecutive,
        "next_review_date": next_date_str,
        "mastered": bool(mastered)
    }
