# create_demo.py
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def run_complete_demo():
    """Run a complete demo of the system"""
    
    print("\n" + "="*70)
    print("COMMUNITY HEALTH TRACKER - COMPLETE DEMONSTRATION")
    print("="*70)
    
    # PART 1: User Registration
    print("\n📝 PART 1: USER REGISTRATION")
    print("-" * 40)
    
    register_data = {
        "username": "demo_user",
        "email": "demo@example.com",
        "password": "Demo123!",
        "password_confirm": "Demo123!",
        "role": "patient",
        "phone_number": "0244123456",
        "region": "Greater Accra",
        "age_group": "25-34"
    }
    
    print("Registering new user...")
    response = requests.post(f"{BASE_URL}/register/", json=register_data)
    if response.status_code == 201:
        print("✅ User registered successfully")
    else:
        print("⚠️ User might already exist, proceeding with login...")
    
    # PART 2: User Login
    print("\n🔐 PART 2: USER LOGIN")
    print("-" * 40)
    
    login_data = {
        "username": "demo_user",
        "password": "Demo123!"
    }
    
    response = requests.post(f"{BASE_URL}/token/", json=login_data)
    if response.status_code == 200:
        token = response.json()['access']
        print("✅ Login successful")
        print(f"🔑 Access Token obtained")
    else:
        print("❌ Login failed. Using default admin...")
        # Try admin login
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/token/", json=login_data)
        token = response.json()['access']
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # PART 3: Get User Profile
    print("\n👤 PART 3: USER PROFILE")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    if response.status_code == 200:
        profile = response.json()
        print("✅ Profile retrieved:")
        print(f"   Username: {profile['username']}")
        print(f"   Email: {profile['email']}")
        if profile['profile']:
            print(f"   Role: {profile['profile']['role']}")
            print(f"   Region: {profile['profile']['region']}")
    
    # PART 4: SYMPTOM ANALYSIS - Multiple Scenarios
    print("\n🏥 PART 4: SYMPTOM ANALYSIS - REAL SCENARIOS")
    print("-" * 40)
    
    scenarios = [
        {
            "name": "Mild Cold",
            "symptoms": "I have runny nose, sneezing, and mild headache for 1 day",
            "temperature": 37.2,
            "duration": 1
        },
        {
            "name": "Malaria Symptoms",
            "symptoms": "High fever, chills, severe headache, body aches for 3 days",
            "temperature": 39.0,
            "duration": 3
        },
        {
            "name": "Emergency - Chest Pain",
            "symptoms": "Chest pain, difficulty breathing, feeling dizzy",
            "temperature": 37.5,
            "duration": 1
        },
        {
            "name": "Stomach Issues",
            "symptoms": "Diarrhea, vomiting, stomach pain for 2 days",
            "temperature": 37.8,
            "duration": 2
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📍 Scenario {i}: {scenario['name']}")
        print(f"   Symptoms: {scenario['symptoms']}")
        
        data = {
            "symptoms_text": scenario['symptoms'],
            "temperature": scenario['temperature'],
            "duration_days": scenario['duration']
        }
        
        response = requests.post(f"{BASE_URL}/analyze/", json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            triage = result['triage_result']
            meds = result.get('medication_recommendations', {})
            
            # Color-coded recommendation
            if triage['recommendation'] == 'home':
                rec_color = "🟢 HOME CARE"
            elif triage['recommendation'] == 'clinic':
                rec_color = "🟡 VISIT CLINIC"
            else:
                rec_color = "🔴 EMERGENCY"
            
            print(f"   → {rec_color}")
            print(f"   → Confidence: {triage['confidence_score']:.0%}")
            print(f"   → Possible: {triage['possible_condition']}")
            
            # Show medications
            if meds and meds.get('medications'):
                print(f"   → Suggested Medications:")
                for med in meds['medications'][:2]:  # Show first 2
                    print(f"     • {med['name']}")
        else:
            print(f"   ❌ Analysis failed")
    
    # PART 5: USER HISTORY
    print("\n📊 PART 5: USER HISTORY")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/history/", headers=headers)
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Found {len(history)} previous consultations")
        for i, entry in enumerate(history[:3], 1):  # Show last 3
            if entry.get('triage_result'):
                date = entry['created_at'][:10]
                rec = entry['triage_result']['recommendation']
                condition = entry['triage_result'].get('possible_condition', 'Unknown')
                print(f"   {i}. {date}: {rec} - {condition}")
    
    # PART 6: OUTBREAK ALERTS
    print("\n🚨 PART 6: ACTIVE OUTBREAK ALERTS")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/outbreaks/")
    if response.status_code == 200:
        alerts = response.json()
        if alerts:
            for alert in alerts:
                level_icon = {
                    'info': 'ℹ️',
                    'watch': '👀',
                    'warning': '⚠️',
                    'emergency': '🚨'
                }.get(alert['alert_level'], '📢')
                
                print(f"\n   {level_icon} {alert['disease_name']} in {alert['region']}")
                print(f"     Level: {alert['alert_level'].upper()}")
                print(f"     Reported: {alert['date_reported']}")
                if alert.get('symptoms'):
                    print(f"     Symptoms: {alert['symptoms'][:100]}...")
        else:
            print("   No active alerts")
    
    # PART 7: MEDICATIONS DATABASE
    print("\n💊 PART 7: AVAILABLE MEDICATIONS")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/medications/")
    if response.status_code == 200:
        medications = response.json()
        print(f"✅ Database contains {len(medications)} medications")
        
        # Group by category
        categories = {}
        for med in medications:
            cat = med.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(med['name'])
        
        for cat, meds in categories.items():
            print(f"\n   {cat}:")
            for med in meds[:3]:  # Show first 3 per category
                print(f"     • {med}")
    
    # PART 8: SYSTEM SUMMARY
    print("\n" + "="*70)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📋 SYSTEM CAPABILITIES DEMONSTRATED:")
    print("   1. User Registration & Authentication")
    print("   2. Profile Management")
    print("   3. AI-Powered Symptom Analysis")
    print("   4. Medication Recommendations")
    print("   5. User Consultation History")
    print("   6. Disease Outbreak Alerts")
    print("   7. Medication Database")
    print("\n⏰ Demo completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)

if __name__ == "__main__":
    run_complete_demo()