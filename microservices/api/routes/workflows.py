from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class WorkflowTrigger(BaseModel):
    workflow_name: str
    payload: dict


class WorkflowResponse(BaseModel):
    status: str
    workflow_id: Optional[str] = None
    result: Optional[dict] = None


@router.post("/trigger", response_model=WorkflowResponse)
async def trigger_workflow(request: WorkflowTrigger):
    return WorkflowResponse(
        status="triggered",
        workflow_id=f"wf_{request.workflow_name}",
        result={"message": f"Workflow {request.workflow_name} submitted to n8n"},
    )


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    return {"workflow_id": workflow_id, "status": "completed", "progress": 100}
