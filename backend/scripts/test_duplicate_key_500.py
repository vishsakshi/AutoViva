import pymongo
from app.models.auth import UserRegisterRequest, UserRole
from app.services.auth_service import auth_service

def test_duplicate_key():
    req = UserRegisterRequest(
        name="Sakshi",
        email="sakshi@gmail.com",
        password="12345678",
        confirm_password="12345678",
        role=UserRole.STUDENT
    )

    print("Submitting first registration for sakshi@gmail.com...")
    try:
        r1 = auth_service.register_user(req)
        print("First Registration Success:", r1.user.email)
    except Exception as e:
        print("First Registration Note:", e)

    print("\nSubmitting duplicate registration for sakshi@gmail.com...")
    try:
        r2 = auth_service.register_user(req)
        print("Duplicate Success:", r2)
    except Exception as e:
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

if __name__ == "__main__":
    test_duplicate_key()
