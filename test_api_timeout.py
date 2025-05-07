import requests
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 2  # 2 seconds timeout

def test_root():
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        print(f"Root endpoint: Status {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("Root endpoint: Request timed out")
    except Exception as e:
        print(f"Error accessing root endpoint: {str(e)}")

if __name__ == "__main__":
    print("Testing API endpoint with timeout...")
    test_root()
