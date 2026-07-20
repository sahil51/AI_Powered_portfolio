import json
import sys
import httpx
from dotenv import dotenv_values

sys.path.insert(0, "ai_assistant")
from agents.meeting_agent import parse_datetime, format_datetime_display
from schemas import MeetingData


def main():
    # Load .env config from the ai_assistant directory
    env_config = dotenv_values("ai_assistant/.env")
    webhook_url = env_config.get("N8N_MEETING_WEBHOOK_URL")

    if not webhook_url:
        print("[!] Warning: N8N_MEETING_WEBHOOK_URL not found in ai_assistant/.env")
        webhook_url = input("Please enter your n8n webhook URL manually: ").strip()
    
    if not webhook_url:
        print("[!] Error: No webhook URL provided. Exiting.")
        return

    print(f"\n[*] Using n8n webhook URL: {webhook_url}")

    # --- Demo validation & parsing ---
    print("\n[*] Validation demos:")
    test_emails = [
        ("mohit@gmail.com", True),
        ("invalid-email", False),
        ("user@domain.c", False),
        ("test@sub.domain.co.in", True),
        ("abc@.com", False),
    ]
    for email, expected in test_emails:
        result = MeetingData.validate_email(email)
        status = "OK" if result == expected else "UNEXPECTED"
        print(f"   Email '{email}' → valid={result} ({status})")

    test_phones = [
        ("+917854128956", True),
        ("9876543210", True),
        ("12345", False),
        ("+1 (555) 123-4567", True),
        ("abc123", False),
    ]
    for phone, expected in test_phones:
        result = MeetingData.validate_phone(phone)
        normalized = MeetingData.normalize_phone(phone) if result else "N/A"
        status = "OK" if result == expected else "UNEXPECTED"
        print(f"   Phone '{phone}' → valid={result}, normalized={normalized} ({status})")

    print("\n[*] Date/Time parsing demos:")
    demos = [
        "20 July 2026, 3PM IST",
        "tomorrow at 5:30 PM",
        "2026-07-17 18:00",
        "next Monday 10am",
    ]
    for d in demos:
        iso = parse_datetime(d)
        display = format_datetime_display(iso) if iso else "(could not parse)"
        print(f"   Raw: {d}")
        print(f"   ISO: {iso}")
        print(f"   Display: {display}\n")

    # Set up dummy payload with ISO-format date (as n8n expects)
    raw_input = "17 July 2026, 9:00 PM IST"
    iso_date = parse_datetime(raw_input)
    payload = {
        "name": "Mohit Sharma",
        "company_name": "Arav Lab Solutions",
        "company_address": "Defence Colony 12a, Ambala Cantt",
        "email": "mohit@gmail.com",
        "contact_number": MeetingData.normalize_phone("+917854128956"),
        "meeting_purpose": "Discuss AI project collaboration",
        "meeting_date_time": iso_date,
        "connection_type": "online",
        "session_id": "test_session_n8n_123"
    }

    print("\n[*] Prepared JSON Payload (validated & normalized):")
    print(json.dumps(payload, indent=4))

    # Allow custom values if the user wants to override
    override = input("\nDo you want to customize any fields? (y/N): ").strip().lower()
    if override == 'y':
        for key in payload.keys():
            user_val = input(f"Enter {key} (press Enter to keep '{payload[key]}'): ").strip()
            if user_val:
                payload[key] = user_val
        print("\n[*] Updated JSON Payload:")
        print(json.dumps(payload, indent=4))

    print("\n[*] Sending POST request to n8n webhook...")
    try:
        # Use a timeout of 15 seconds as configured in the agent
        with httpx.Client(timeout=15.0) as client:
            response = client.post(webhook_url, json=payload)
            
            print(f"\n[+] Response Status Code: {response.status_code}")
            print("[+] Response Headers:")
            for k, v in response.headers.items():
                print(f"    {k}: {v}")
            
            print("\n[+] Response Body (Raw Text):")
            print(response.text)
            
            try:
                data = response.json()
                print("\n[+] Response Body (Parsed JSON):")
                print(json.dumps(data, indent=4))
            except json.JSONDecodeError:
                print("\n[!] Response body is not valid JSON.")
    except Exception as e:
        print(f"\n[!] Error connecting to webhook: {e}")

if __name__ == "__main__":
    main()
