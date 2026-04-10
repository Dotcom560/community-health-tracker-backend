import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_registration():
    """Test user registration"""
    url = f"{BASE_URL}/register/"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "role": "patient",
        "region": "Greater Accra",
        "age_group": "19-35"
    }
    
    response = requests.post(url, json=data)
    print("Registration:", response.status_code, response.json())
    return response.json()

def test_login():
    """Test login"""
    url = f"{BASE_URL}/token/"
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(url, json=data)
    print("Login:", response.status_code)
    if response.status_code == 200:
        tokens = response.json()
        print("Got access token")
        return tokens['access']
    return None

def test_analyze_symptoms(token):
    """Test symptom analysis"""
    url = f"{BASE_URL}/analyze/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "symptoms_text": "I have fever and headache for 2 days",
        "temperature": 38.5,
        "duration_days": 2
    }
    
    response = requests.post(url, json=data, headers=headers)
    print("Symptom Analysis:", response.status_code)
    if response.status_code == 201:
        result = response.json()
        print(f"Recommendation: {result['triage_result']['recommendation']}")
        print(f"Confidence: {result['triage_result']['confidence_score']}")
        print(f"Condition: {result['triage_result']['possible_condition']}")
        return result
    return None

def test_get_outbreaks():
    """Test outbreak alerts"""
    url = f"{BASE_URL}/outbreaks/"
    response = requests.get(url)
    print("Outbreak Alerts:", response.status_code)
    if response.status_code == 200:
        alerts = response.json()
        print(f"Found {len(alerts)} active alerts")
    return response.json()

if __name__ == "__main__":
    print("="*50)
    print("Testing Community Health Tracker API")
    print("="*50)
    
    # Test registration
    print("\n1. Testing Registration...")
    test_registration()
    
    # Test login
    print("\n2. Testing Login...")
    token = test_login()
    
    if token:
        # Test symptom analysis
        print("\n3. Testing Symptom Analysis...")
        test_analyze_symptoms(token)
    
    # Test outbreak alerts
    print("\n4. Testing Outbreak Alerts...")
    test_get_outbreaks()
    
    print("\n" + "="*50)
    print("Tests completed!")