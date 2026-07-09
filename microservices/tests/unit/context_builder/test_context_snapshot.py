from datetime import datetime, timedelta, timezone

from application.context_builder.models import BuiltContext, ContextLayerResult, ContextMetadata
from application.context_builder.snapshot import ContextSnapshot


class TestContextSnapshot:
    def test_create_and_restore(self):
        context = BuiltContext(
            layers={"system": ContextLayerResult(name="system", data={"key": "val"})},
            metadata=ContextMetadata(total_tokens=10, max_tokens=100),
        )
        snapshot = ContextSnapshot(context=context, label="test-snapshot")
        restored = snapshot.restore()
        assert restored is context

    def test_is_expired(self):
        old_time = datetime.now(timezone.utc) - timedelta(seconds=600)
        snapshot = ContextSnapshot(captured_at=old_time)
        assert snapshot.is_expired(ttl_seconds=300)

    def test_not_expired(self):
        snapshot = ContextSnapshot()
        assert not snapshot.is_expired(ttl_seconds=300)

    def test_to_dict(self):
        context = BuiltContext(
            layers={"system": ContextLayerResult(name="system", data={})},
            metadata=ContextMetadata(total_tokens=0, max_tokens=100),
        )
        snapshot = ContextSnapshot(context=context, label="test")
        d = snapshot.to_dict()
        assert d["label"] == "test"
        assert d["context"] is not None
