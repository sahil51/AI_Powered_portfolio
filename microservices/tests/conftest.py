import pytest


@pytest.fixture
def meeting_data():
    return {
        "full_name": "John Doe",
        "email": "john@example.com",
        "contact_number": "+1234567890",
        "company_name": "ACME Corporation",
        "company_address": "123 Business Ave",
        "meeting_purpose": "Discuss AI project",
        "preferred_date": "2024-02-15",
        "preferred_time": "10:00",
        "timezone": "America/New_York",
        "meeting_type": "google_meet",
    }


@pytest.fixture
def lead_data():
    return {
        "name": "Jane Smith",
        "email": "jane@techcorp.com",
        "company": "TechCorp Inc.",
    }
