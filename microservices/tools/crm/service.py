from tools.base import BaseTool


class CreateLeadTool(BaseTool):
    name = "create_lead"
    description = "Create a lead in CRM. Delegates to n8n."

    async def execute(self, lead_data: dict) -> dict:
        return {"delegated": True, "workflow": "n8n/crm/create_lead"}


class QualifyLeadTool(BaseTool):
    name = "qualify_lead"
    description = "Qualify a lead based on collected information. Returns qualification score."

    async def execute(self, lead_data: dict) -> dict:
        score = 0.0
        if lead_data.get("company"):
            score += 0.3
        if lead_data.get("phone"):
            score += 0.2
        if lead_data.get("meeting_purpose"):
            score += 0.3
        if len(lead_data.get("notes", "")) > 50:
            score += 0.2
        qualified = score >= 0.5
        return {"qualified": qualified, "score": score}
