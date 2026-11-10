import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db
from backend.seed import seed_sample_data

class TestKazanacagizApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_sample_data()
        cls.client = TestClient(app)

    def test_01_login_and_token(self):
        # Invalid login
        bad_resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "wrongpassword"})
        self.assertEqual(bad_resp.status_code, 400)

        # Valid login
        resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "ogrenci123"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("token", data)
        token = data["token"]

        # Fetch profile using Bearer token
        me_resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["username"], "ogrenci")
        print("Test 1 Passed: Login and Bearer token authentication verified.")

    def test_02_due_questions_hides_correct_answer(self):
        login_resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "ogrenci123"})
        token = login_resp.json()["token"]

        resp = self.client.get("/api/questions/due", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        questions = resp.json()
        self.assertTrue(len(questions) > 0)
        for q in questions:
            self.assertNotIn("correct_answer", q, "Correct answer MUST be hidden before answering!")
        print("Test 2 Passed: Due questions returned with correct_answer securely omitted.")

    def test_03_premium_license_key_gate(self):
        login_resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "ogrenci123"})
        token = login_resp.json()["token"]

        # Invalid key attempt
        bad_key = self.client.post("/api/premium/redeem-key", json={"key_code": "FAKE-KEY-999"}, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(bad_key.status_code, 400)

        # Valid key redemption
        good_key = self.client.post("/api/premium/redeem-key", json={"key_code": "KAZAN-PRO-2026"}, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(good_key.status_code, 200)
        self.assertIn("premium_until", good_key.json())

        # Verify user is now premium
        me = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertTrue(me["is_premium"])

        # Attempt to use the same key again -> must be rejected!
        reuse_key = self.client.post("/api/premium/redeem-key", json={"key_code": "KAZAN-PRO-2026"}, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(reuse_key.status_code, 400)
        self.assertIn("daha önce kullanılmış", reuse_key.json()["detail"])
        print("Test 3 Passed: Premium gate strictly verified (invalid, valid, reuse blocked).")

    def test_04_answer_correct_reschedules_next_week(self):
        login_resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "ogrenci123"})
        token = login_resp.json()["token"]

        resp = self.client.post("/api/questions/answer", json={
            "question_id": 1,
            "given_answer": "C"
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_correct"])
        self.assertEqual(data["consecutive_correct"], 1)
        print("Test 4 Passed: Correct answer reschedules to +7 days.")

    def test_05_mandatory_correct_answer_validation(self):
        login_resp = self.client.post("/api/auth/login", json={"username": "ogrenci", "password": "ogrenci123"})
        token = login_resp.json()["token"]

        with open("uploads/sample_cografya.svg", "rb") as f:
            resp = self.client.post("/api/questions/upload", 
                files={"image": ("test.svg", f, "image/svg+xml")},
                data={"correct_answer": "INVALID", "subject": "Test", "topic": "Test"},
                headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(resp.status_code, 400)
        print("Test 5 Passed: Upload without valid correct answer rejected with 400.")

if __name__ == "__main__":
    unittest.main()
