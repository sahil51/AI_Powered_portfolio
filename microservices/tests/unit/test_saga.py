import pytest

from saga.orchestrator import MeetingSaga, SagaOrchestrator, SagaStep


class TestSagaOrchestrator:
    @pytest.mark.asyncio
    async def test_successful_saga(self):
        saga = SagaOrchestrator()
        executed = []

        async def action(ctx):
            executed.append("action")
            return {"status": "done"}

        async def compensation(ctx):
            executed.append("compensation")

        saga.add_step(SagaStep("step1", action, compensation))
        result = await saga.execute({})
        assert result["step1"]["status"] == "done"
        assert executed == ["action"]

    @pytest.mark.asyncio
    async def test_saga_rollback(self):
        saga = SagaOrchestrator()
        executed = []

        async def action1(ctx):
            executed.append("action1")
            return {"status": "done"}

        async def comp1(ctx):
            executed.append("comp1")

        async def action2(ctx):
            executed.append("action2")
            raise Exception("Step 2 failed")

        async def comp2(ctx):
            executed.append("comp2")

        saga.add_step(SagaStep("step1", action1, comp1))
        saga.add_step(SagaStep("step2", action2, comp2))

        with pytest.raises(Exception, match="Step 2 failed"):
            await saga.execute({})

        assert executed == ["action1", "action2", "comp1"]

    def test_meeting_saga_creation(self):
        saga = MeetingSaga.create_schedule_saga()
        assert len(saga.steps) == 4
        assert saga.steps[0].name == "create_calendar_event"
        assert saga.steps[-1].name == "save_crm"
