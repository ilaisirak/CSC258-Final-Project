import time
import random
from io import BytesIO
from locust import HttpUser, task, between

# ------------------------------------------------------------------
# CONFIGURATION – change these IDs to match your pre‑seeded data
# ------------------------------------------------------------------
CLASS_ID = "84c83d7b-b87b-4e01-83c3-a341e2375d94"        # Must create your own and update here
ASSIGNMENT_ID = "fd3d179b-b234-4694-85d2-88425fbcf6b8"   # Must create your own and update here
# ------------------------------------------------------------------

class StudentUser(HttpUser):
    """
    Simulates a student who logs in (auto‑registers if new),
    views their assignments, and submits work to one assignment.
    """
    wait_time = between(1, 5)   # think time between tasks

    def on_start(self):
        # Generate a unique identity for this simulated user
        self.user_name = f"student_{random.randint(1000, 9999)}"
        self.email = f"{self.user_name}@example.edu"
        self.role = "student"

        # 1. Create the user (if already exists, backend returns 409 – we ignore)
        with self.client.post("/api/users",
                              json={"name": self.user_name,
                                    "email": self.email,
                                    "role": self.role},
                              catch_response=True) as resp:
            if resp.status_code not in (200, 409):   # 409 = already exists
                resp.failure(f"Unexpected status during user creation: {resp.status_code}")

        # 2. Sign in to obtain the user ID (stored in the response body)
        signin_resp = self.client.post("/api/users/sign-in",
                                       json={"role": self.role,
                                             "name": self.user_name})
        if signin_resp.status_code == 200:
            self.user_id = signin_resp.json().get("id")
            # All subsequent requests must carry the user ID header
            self.client.headers.update({"X-User-Id": self.user_id})
        else:
            signin_resp.failure("Could not sign in")

    @task(3)
    def list_assignments(self):
        """Fetch all assignments visible to the student."""
        with self.client.get("/api/assignments",
                             catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Got status {resp.status_code}")

    @task(1)
    def submit_assignment(self):
        """Submit a dummy text file to the pre‑seeded assignment."""
        # Simulated file content
        content = b"This is a submission from a load test."
        files = {"file": ("submission.txt", BytesIO(content), "text/plain")}
        # Multipart form data – do NOT set Content-Type header manually
        with self.client.post("/api/submit",
                              data={"assignmentId": ASSIGNMENT_ID,
                                    "studentId": self.user_id,
                                    "studentName": self.user_name},
                              files=files,
                              catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Submission failed: {resp.status_code}")


class ProfessorUser(HttpUser):
    """
    Simulates a professor who logs in, views classes, and grades
    a submission on the pre‑seeded assignment.
    """
    wait_time = between(2, 6)

    def on_start(self):
        self.user_name = f"professor_{random.randint(1000, 9999)}"
        self.email = f"{self.user_name}@example.edu"
        self.role = "professor"

        # Create / ignore if exists
        with self.client.post("/api/users",
                              json={"name": self.user_name,
                                    "email": self.email,
                                    "role": self.role},
                              catch_response=True) as resp:
            if resp.status_code not in (200, 409):
                resp.failure(f"Unexpected status during user creation: {resp.status_code}")

        # Sign in
        signin_resp = self.client.post("/api/users/sign-in",
                                       json={"role": self.role,
                                             "name": self.user_name})
        if signin_resp.status_code == 200:
            self.user_id = signin_resp.json().get("id")
            self.client.headers.update({"X-User-Id": self.user_id})
        else:
            signin_resp.failure("Could not sign in")

        # The professor also needs a submission to grade.
        # We will fetch the list of submissions and pick the first one.
        # Store its ID for later grading tasks.
        self.submission_id = None

    @task(2)
    def list_classes(self):
        """View all classes owned by this professor."""
        with self.client.get("/api/classes", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"List classes failed: {resp.status_code}")

    @task(1)
    def grade_submission(self):
        """
        Fetch submissions for the pre‑seeded assignment,
        pick the first submission, and assign a random grade.
        """
        # 1. Get submissions list
        list_resp = self.client.get(
            f"/api/submissions?assignmentId={ASSIGNMENT_ID}",
            catch_response=True)
        if list_resp.status_code != 200:
            list_resp.failure("Could not fetch submissions")
            return
        submissions = list_resp.json()
        if not submissions:
            return   # nothing to grade

        sub = random.choice(submissions)
        sub_id = sub["id"]       # camelCase due to keysToCamelCase in frontend,
                                 # but in our direct API the response is still snake_case
                                 # if we haven't added the conversion middleware.
                                 # Since we are calling the backend directly, fields are
                                 # snake_case: "assignment_id", "student_id", etc.
                                 # We must adjust here.
        # Actually, the backend returns snake_case. The HTTP adapter in the frontend
        # does camelCase conversion, but Locust calls the API directly, so we must
        # use the original snake_case field names.
        sub_id = sub.get("id")  # 'id' is always 'id'
        # Score: random between 0 and assignment points (assume 100)
        score = random.randint(0, 100)

        # 2. Upsert grade
        grade_payload = {
            "submissionId": sub_id,
            "score": score,
            "pointsPossible": 100,
            "feedback": "Good job!" if score > 50 else "Needs improvement.",
            "gradedById": self.user_id
        }
        grade_resp = self.client.post("/api/grading",
                                      json=grade_payload,
                                      catch_response=True)
        if grade_resp.status_code == 200:
            grade_resp.success()
        else:
            grade_resp.failure(f"Grading failed: {grade_resp.status_code}")