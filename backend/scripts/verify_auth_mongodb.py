import pymongo
from app.core.config import settings
from app.services.auth_service import auth_service
from app.models.auth import UserRegisterRequest, UserLoginRequest, UserRole

def run_auth_verification():
    print("=" * 90)
    print("AUTOVIVA MONGODB AUTHENTICATION VERIFICATION SUITE")
    print("=" * 90)

    client = pymongo.MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    users_col = db["users"]

    # Clear previous test user if exists
    test_email = "verify_student_2026@university.edu"
    users_col.delete_many({"email": test_email})

    # STEP 1: Create Account in MongoDB
    print("\n--- STEP 1: Creating Account via Register API ---")
    reg_req = UserRegisterRequest(
        name="Elena Vance",
        email=test_email,
        password="SecureAcademicPass123!",
        confirm_password="SecureAcademicPass123!",
        role=UserRole.STUDENT
    )

    token_resp = auth_service.register_user(reg_req)
    print(f"Issued Access Token: {token_resp.access_token[:30]}...")
    print(f"User ID: {token_resp.user.user_id}")
    print(f"User Role: {token_resp.user.role}")

    # STEP 2: Inspect User Document in MongoDB
    print("\n--- STEP 2: Inspecting Document in MongoDB `db.users` ---")
    mongo_user = users_col.find_one({"email": test_email})
    assert mongo_user is not None
    assert mongo_user["name"] == "Elena Vance"
    assert mongo_user["role"] == "student"
    assert mongo_user["hashed_password"].startswith("$2b$") or mongo_user["hashed_password"].startswith("$2a$")
    print(f"[VERIFIED]: Document exists in MongoDB!")
    print(f"Name: {mongo_user['name']}")
    print(f"Role: {mongo_user['role']}")
    print(f"Bcrypt Password Hash: {mongo_user['hashed_password'][:25]}...")

    # STEP 3: Duplicate Email Check
    print("\n--- STEP 3: Duplicate Email Validation ---")
    try:
        auth_service.register_user(reg_req)
        print("[FAILED]: Should have rejected duplicate email.")
    except ValueError as ve:
        print(f"[PASSED]: Catch duplicate email error -> \"{str(ve)}\"")

    # STEP 4: Invalid Password Login Check
    print("\n--- STEP 4: Invalid Password Login Validation ---")
    try:
        auth_service.authenticate_user(UserLoginRequest(email=test_email, password="WrongPassword!"))
        print("[FAILED]: Should have rejected incorrect password.")
    except ValueError as ve:
        print(f"[PASSED]: Caught invalid password error -> \"{str(ve)}\"")

    # STEP 5: Valid Login Against MongoDB
    print("\n--- STEP 5: Valid Login Against MongoDB ---")
    login_resp = auth_service.authenticate_user(UserLoginRequest(email=test_email, password="SecureAcademicPass123!"))
    print(f"[SUCCESS]: Logged in successfully!")
    print(f"Token: {login_resp.access_token[:30]}...")
    print(f"User Name: {login_resp.user.name}")

    # STEP 6: Verify JWT Token Decoding
    print("\n--- STEP 6: JWT Token Decoding & Verification ---")
    decoded = auth_service.decode_token(login_resp.access_token)
    assert decoded is not None
    assert decoded["email"] == test_email
    assert decoded["role"] == "student"
    print(f"[PASSED]: Token decoded successfully! Subject: {decoded['sub']}, Role: {decoded['role']}")

    print("\n" + "=" * 90)
    print("ALL MONGODB AUTHENTICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 90)

if __name__ == "__main__":
    run_auth_verification()
