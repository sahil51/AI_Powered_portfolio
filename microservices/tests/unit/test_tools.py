import pytest

from tools.crm.service import QualifyLeadTool
from tools.meeting.service import ValidateMeetingDetailsTool


class TestValidateMeetingDetailsTool:
    @pytest.mark.asyncio
    async def test_valid_data(self):
        tool = ValidateMeetingDetailsTool()
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "contact_number": "+1234567890",
            "company_name": "ACME",
            "company_address": "123 St",
            "meeting_purpose": "Discuss",
            "preferred_date": "2024-01-15",
            "preferred_time": "10:00",
            "timezone": "UTC",
            "meeting_type": "google_meet",
        }
        result = await tool.execute(data)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_missing_fields(self):
        tool = ValidateMeetingDetailsTool()
        data = {"full_name": "John Doe"}
        result = await tool.execute(data)
        assert result["valid"] is False
        assert "email" in result["missing_fields"]


class TestQualifyLeadTool:
    @pytest.mark.asyncio
    async def test_qualified_lead(self):
        tool = QualifyLeadTool()
        data = {"company": "ACME", "phone": "+123", "meeting_purpose": "Discuss project partnership", "notes": "x" * 60}
        result = await tool.execute(data)
        assert result["qualified"] is True
        assert result["score"] >= 0.5

    @pytest.mark.asyncio
    async def test_unqualified_lead(self):
        tool = QualifyLeadTool()
        data = {"email": "john@example.com"}
        result = await tool.execute(data)
        assert result["qualified"] is False
