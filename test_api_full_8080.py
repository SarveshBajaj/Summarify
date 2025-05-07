import requests
import json

BASE_URL = "http://localhost:8080"
TIMEOUT = 10  # 10 seconds timeout

def test_root():
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        print(f"Root endpoint: Status {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("Root endpoint: Request timed out")
    except Exception as e:
        print(f"Error accessing root endpoint: {str(e)}")

def test_docs():
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        print(f"Docs endpoint: Status {response.status_code}")
        print(f"Response length: {len(response.text)} characters")
    except requests.exceptions.Timeout:
        print("Docs endpoint: Request timed out")
    except Exception as e:
        print(f"Error accessing docs endpoint: {str(e)}")

def test_signup():
    try:
        data = {
            "username": "testuser",
            "password": "testpassword",
            "email": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/signup", json=data, timeout=TIMEOUT)
        print(f"Signup endpoint: Status {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("Signup endpoint: Request timed out")
    except Exception as e:
        print(f"Error accessing signup endpoint: {str(e)}")

def test_login():
    try:
        data = {
            "username": "testuser",
            "password": "testpassword"
        }
        response = requests.post(
            f"{BASE_URL}/login", 
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT
        )
        print(f"Login endpoint: Status {response.status_code}")
        print(f"Response: {response.text}")
        return response.json().get("access_token") if response.status_code == 200 else None
    except requests.exceptions.Timeout:
        print("Login endpoint: Request timed out")
        return None
    except Exception as e:
        print(f"Error accessing login endpoint: {str(e)}")
        return None

if __name__ == "__main__":
    print("Testing API endpoints on port 8080...")
    test_root()
    print("\n" + "-"*50 + "\n")
    test_docs()
    print("\n" + "-"*50 + "\n")
    test_signup()
    print("\n" + "-"*50 + "\n")
    test_login()
