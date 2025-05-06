import requests
import json

# Base URL
base_url = "http://localhost:8000"

# 1. Sign up a test user
def signup():
    signup_url = f"{base_url}/signup"
    signup_data = {
        "username": "testuser123",
        "password": "password123"
    }
    
    response = requests.post(signup_url, json=signup_data)
    print(f"Signup Response: {response.status_code}")
    if response.status_code == 201:
        return response.json()["access_token"]
    else:
        print(f"Error: {response.text}")
        return None

# 2. Login with the test user
def login():
    login_url = f"{base_url}/login"
    login_data = {
        "username": "testuser123",
        "password": "password123"
    }
    
    response = requests.post(
        login_url, 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Login Response: {response.status_code}")
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error: {response.text}")
        return None

# 3. Test summarization
def test_summarization(token, youtube_url):
    summarize_url = f"{base_url}/summarize"
    summarize_data = {
        "url": youtube_url,
        "max_length": 1000
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(summarize_url, json=summarize_data, headers=headers)
    print(f"Summarize Response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nSummary:")
        print(result["summary"])
        print(f"\nValid: {result['valid']}")
        print(f"Metadata: {json.dumps(result['metadata'], indent=2)}")
        return result
    else:
        print(f"Error: {response.text}")
        return None

# Main test flow
def main():
    # Try to sign up (may fail if user exists)
    token = signup()
    
    # If signup fails, try login
    if not token:
        token = login()
    
    if token:
        # Test with the provided YouTube URL
        youtube_url = "https://www.youtube.com/watch?v=fXizBc03D7E"
        test_summarization(token, youtube_url)
    else:
        print("Failed to get authentication token")

if __name__ == "__main__":
    main()
