import requests
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1/webhook/whatsapp"

# Publicly available sample invoice (or generic image)
# Using a stable placeholder image for reliability
SAMPLE_IMAGE_URL = "https://templates.invoicehome.com/invoice-template-us-neat-750px.png"

def simulate_twilio_message():
    print(f"📡 Simulating Incoming Twilio Message...")
    print(f"   Target: {BASE_URL}")
    print(f"   Media: {SAMPLE_IMAGE_URL}")
    
    # Twilio sends data as form-urlencoded (usually), but requests.post with 'data' does this.
    # Key fields Twilio sends:
    payload = {
        "From": "whatsapp:+14155552345",
        "Body": "Here is my invoice",
        "MediaUrl0": SAMPLE_IMAGE_URL,
        "NumMedia": "1",
        "ProfileName": "Simulation User"
    }
    
    try:
        response = requests.post(BASE_URL, data=payload)
        
        if response.status_code == 200:
            print(f"✅ Success! Server accepted the webhook.")
            print(f"   Response: {response.json()}")
            print("\nCheck system logs for 'Downloaded Twilio media' and AI processing.")
        else:
            print(f"❌ Failed. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending request: {e}")

if __name__ == "__main__":
    simulate_twilio_message()
