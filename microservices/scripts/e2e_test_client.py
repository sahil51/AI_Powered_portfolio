import urllib.request
import json
import sys

def send_chat_message(message: str, user_id: str = "john_doe") -> dict:
    url = "http://localhost:8000/chat/message/sync"
    payload = {
        "message": message,
        "user_type": "visitor",
        "user_id": user_id
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        print(f"Error calling API: {e}")
        return {}

def main():
    print("=== STARTING LIVE E2E USER SIMULATION ===")
    
    # Step 1: Send Greeting and Meeting Request
    user_msg = "Hello, my name is John from ACME. I would like to schedule a virtual Google Meet with Sahil next Monday at 10:00 AM to discuss the project."
    print(f"\nUser says: '{user_msg}'")
    
    response = send_chat_message(user_msg)
    print("\nAssistant responds:")
    print(json.dumps(response, indent=2))
    
    if "response" in response:
        print("\n=== E2E CHAT SIMULATION COMPLETE ===")
        sys.exit(0)
    else:
        print("\n=== E2E CHAT SIMULATION FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
