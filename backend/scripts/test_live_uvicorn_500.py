import requests

def test_live_server():
    url = "http://localhost:8000/api/auth/register"
    payload = {
        "name": "Sakshi Live",
        "email": "sakshi_live_test_2026@gmail.com",
        "password": "12345678",
        "confirm_password": "12345678",
        "role": "student"
    }

    print(f"Sending POST request to live server at {url}...")
    try:
        res = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {res.status_code}")
        print(f"Response Body: {res.text}")
    except Exception as e:
        print(f"Connection error to live server: {e}")

if __name__ == "__main__":
    test_live_server()
