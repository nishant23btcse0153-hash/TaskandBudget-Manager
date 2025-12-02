"""Test if home page loads correctly"""
from app import app

app.config['TESTING'] = True

with app.test_client() as client:
    try:
        response = client.get('/')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 500:
            print("\n❌ 500 ERROR FOUND!")
            print("Response content:")
            print(response.data.decode('utf-8'))
        elif response.status_code == 200:
            print("✅ Home page loads successfully!")
            print("First 300 characters:")
            print(response.data.decode('utf-8')[:300])
        else:
            print(f"Unexpected status: {response.status_code}")
            print(response.data.decode('utf-8')[:500])
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
