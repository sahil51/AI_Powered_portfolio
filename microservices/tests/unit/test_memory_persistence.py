
from infrastructure.memory.models import MemoryAuditModel, MemoryDBModel, MemoryRecordDBModel, MemoryTagModel


class TestMemoryDBModels:
    def test_memory_db_model_tablename(self):
        assert MemoryDBModel.__tablename__ == "memories"

    def test_memory_db_model_columns(self):
        model = MemoryDBModel(
            user_id="user-1",
            value="test memory",
            category="fact",
            scope="user",
            status="active",
        )
        assert model.user_id == "user-1"
        assert model.value == "test memory"
        assert model.category == "fact"
        assert model.scope == "user"

    def test_memory_db_model_with_optional_fields(self):
        model = MemoryDBModel(
            user_id="user-1",
            value="test",
            category="preference",
            scope="user",
            status="active",
            key_namespace="prefs",
            key_value="theme",
            conversation_id="conv-1",
            session_id="session-1",
            memory_type="long_term",
            priority="high",
            confidence="certain",
            importance="critical",
            source="user_input",
            tags=["important", "follow-up"],
        )
        assert model.key_namespace == "prefs"
        assert model.conversation_id == "conv-1"
        assert model.tags == ["important", "follow-up"]

    def test_memory_record_db_model(self):
        import uuid
        model = MemoryRecordDBModel(
            memory_id=uuid.uuid4(),
            value="record value",
            record_type="snapshot",
        )
        assert model.value == "record value"
        assert model.record_type == "snapshot"

    def test_memory_tag_model(self):
        import uuid
        model = MemoryTagModel(
            memory_id=uuid.uuid4(),
            tag="important",
        )
        assert model.tag == "important"

    def test_memory_audit_model(self):
        import uuid
        model = MemoryAuditModel(
            memory_id=uuid.uuid4(),
            action="update",
            previous_value="old",
            new_value="new",
            user_id="user-1",
        )
        assert model.action == "update"
        assert model.previous_value == "old"

    def test_memory_db_model_unique_constraint(self):
        constraints = MemoryDBModel.__table_args__
        constraint_names = []
        if isinstance(constraints, tuple):
            for c in constraints:
                if hasattr(c, "name"):
                    constraint_names.append(c.name)
                elif isinstance(c, dict):
                    constraint_names.extend(c.keys())
        assert any("uq_memory_user_key" in str(n) for n in constraint_names)

    def test_memory_tag_model_unique_constraint(self):
        constraints = MemoryTagModel.__table_args__
        constraint_names = []
        if isinstance(constraints, tuple):
            for c in constraints:
                if hasattr(c, "name"):
                    constraint_names.append(c.name)
                elif isinstance(c, dict):
                    constraint_names.extend(c.keys())
        assert any("uq_memory_tag" in str(n) for n in constraint_names)

    def test_memory_db_model_relationships(self):
        assert hasattr(MemoryDBModel, "records")
        assert hasattr(MemoryDBModel, "tags_list")
        assert hasattr(MemoryDBModel, "audits")
        assert hasattr(MemoryRecordDBModel, "memory")
        assert hasattr(MemoryTagModel, "memory")
        assert hasattr(MemoryAuditModel, "memory")
