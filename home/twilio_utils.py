import os
from twilio.rest import Client
from django.conf import settings

def get_twilio_client():
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        print("Twilio credentials not found in environment variables.")
        return None
        
    return Client(account_sid, auth_token)

def send_whatsapp_message(to_number: str, body: str):
    """
    Sends a WhatsApp message using Twilio.
    to_number must be formatted as 'whatsapp:+1234567890'
    """
    client = get_twilio_client()
    if not client:
        print(f"Mock send WhatsApp to {to_number}: {body}")
        return False
        
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    if not from_number:
        print("TWILIO_WHATSAPP_NUMBER not set in environment.")
        return False
        
    try:
        message = client.messages.create(
            from_=from_number,
            body=body,
            to=to_number
        )
        print(f"Sent WhatsApp message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False

def notify_user_via_whatsapp(message: str):
    """
    Sends a notification to the user's personal WhatsApp number.
    """
    user_number = os.environ.get("MY_WHATSAPP_NUMBER")
    if not user_number:
        print(f"Mock notify user: {message}")
        return False
        
    return send_whatsapp_message(user_number, message)
