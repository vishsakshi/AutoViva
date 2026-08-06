import traceback
from app.models.auth import UserRegisterRequest, UserRole
from app.services.auth_service import auth_service

def reproduce():
    print("Reproducing user registration with exact payload...")
    req = UserRegisterRequest(
        name="Sakshi",
        email="sakshi@gmail.com",
        password="12345678",
        confirm_password="12345678",
        role=UserRole.STUDENT
    )

    try:
        res = auth_service.register_user(req)
        print("Registration result:", res)
    except Exception as e:
        print("\nEXCEPTIONAL TRACEBACK CAUSING HTTP 500:")
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
