from typing import Callable

from monitoring.logger import logger


class SagaStep:
    def __init__(self, name: str, action: Callable, compensation: Callable):
        self.name = name
        self.action = action
        self.compensation = compensation


class SagaOrchestrator:
    def __init__(self):
        self.steps: list[SagaStep] = []
        self.executed_steps: list[SagaStep] = []

    def add_step(self, step: SagaStep) -> None:
        self.steps.append(step)

    async def execute(self, context: dict) -> dict:
        self.executed_steps = []
        results = {}

        for step in self.steps:
            try:
                result = await step.action(context)
                results[step.name] = result
                self.executed_steps.append(step)
                logger.info(f"Saga step '{step.name}' completed")
            except Exception as e:
                logger.error(f"Saga step '{step.name}' failed: {e}")
                await self._rollback(context)
                raise SagaExecutionError(f"Step '{step.name}' failed: {e}")

        return results

    async def _rollback(self, context: dict) -> None:
        logger.warning(f"Rolling back {len(self.executed_steps)} steps")
        for step in reversed(self.executed_steps):
            try:
                await step.compensation(context)
                logger.info(f"Saga compensation '{step.name}' completed")
            except Exception as e:
                logger.error(f"Saga compensation '{step.name}' failed: {e}")


class SagaExecutionError(Exception):
    pass


class MeetingSaga:
    @staticmethod
    def create_schedule_saga() -> SagaOrchestrator:
        saga = SagaOrchestrator()

        async def create_calendar_event(ctx: dict) -> dict:
            return {"event_id": "cal_event_123", "status": "created"}

        async def rollback_calendar_event(ctx: dict) -> dict:
            return {"event_id": ctx.get("event_id"), "status": "deleted"}

        async def save_to_database(ctx: dict) -> dict:
            return {"meeting_id": "meeting_123", "status": "saved"}

        async def rollback_database(ctx: dict) -> dict:
            return {"meeting_id": ctx.get("meeting_id"), "status": "deleted"}

        async def send_email(ctx: dict) -> dict:
            return {"email_id": "email_123", "status": "sent"}

        async def rollback_email(ctx: dict) -> dict:
            return {"email_id": ctx.get("email_id"), "status": "cancelled"}

        async def save_crm(ctx: dict) -> dict:
            return {"lead_id": "lead_123", "status": "created"}

        async def rollback_crm(ctx: dict) -> dict:
            return {"lead_id": ctx.get("lead_id"), "status": "deleted"}

        saga.add_step(SagaStep("create_calendar_event", create_calendar_event, rollback_calendar_event))
        saga.add_step(SagaStep("save_to_database", save_to_database, rollback_database))
        saga.add_step(SagaStep("send_email", send_email, rollback_email))
        saga.add_step(SagaStep("save_crm", save_crm, rollback_crm))

        return saga
