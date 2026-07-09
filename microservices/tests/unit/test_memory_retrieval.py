
from application.memory.retrieval import (
    CONFIDENCE_ORDER,
    IMPORTANCE_ORDER,
    MemoryFilter,
    MemoryFilterEngine,
    MemoryPage,
    MemoryQueryEngine,
    MemoryRankingEngine,
    MemoryResult,
    MemorySelectionEngine,
    MemorySort,
    MemorySortField,
    MemorySortOrder,
)
from domain.memory.aggregate import Memory
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryPriority,
    MemoryScope,
)


class TestMemoryRankingEngine:
    def setup_method(self) -> None:
        self.engine = MemoryRankingEngine()

    def test_rank_by_importance(self):
        memories = self._make_memories([
            ("low", "medium", "medium"),
            ("critical", "medium", "medium"),
            ("high", "medium", "medium"),
        ])
        ranked = self.engine.rank(memories, MemorySort(field=MemorySortField.IMPORTANCE))
        assert ranked[0].importance == MemoryImportance.CRITICAL
        assert ranked[1].importance == MemoryImportance.HIGH
        assert ranked[2].importance == MemoryImportance.LOW

    def test_rank_by_confidence(self):
        memories = self._make_memories([
            ("medium", "low", "medium"),
            ("medium", "certain", "medium"),
            ("medium", "high", "medium"),
        ])
        ranked = self.engine.rank(memories, MemorySort(field=MemorySortField.CONFIDENCE))
        assert ranked[0].confidence == MemoryConfidence.CERTAIN
        assert ranked[1].confidence == MemoryConfidence.HIGH

    def test_rank_by_priority(self):
        memories = self._make_memories([
            ("medium", "medium", "low"),
            ("medium", "medium", "critical"),
            ("medium", "medium", "high"),
        ])
        ranked = self.engine.rank(memories, MemorySort(field=MemorySortField.PRIORITY))
        assert ranked[0].priority == MemoryPriority.CRITICAL
        assert ranked[1].priority == MemoryPriority.HIGH

    def test_rank_by_recency(self):
        m1 = Memory(user_id="u1", value="old")
        m2 = Memory(user_id="u1", value="new")
        import time
        time.sleep(0.01)
        m2 = Memory(user_id="u1", value="new")
        m2.activate()
        ranked = self.engine.rank([m1, m2], MemorySort(field=MemorySortField.RECENCY, order=MemorySortOrder.DESC))
        assert len(ranked) == 2

    def test_business_rules_ranking(self):
        memories = self._make_memories([
            ("low", "low", "low"),
            ("critical", "certain", "critical"),
        ])
        ranked = self.engine._rank_by_business_rules(memories)
        first = ranked[0]
        assert first.importance == MemoryImportance.CRITICAL

    def test_rank_empty_list(self):
        assert self.engine.rank([]) == []

    @staticmethod
    def _make_memories(specs: list[tuple[str, str, str]]) -> list[Memory]:
        memories = []
        for imp, conf, pri in specs:
            m = Memory(
                user_id="u1",
                value="test",
                importance=MemoryImportance(imp),
                confidence=MemoryConfidence(conf),
                priority=MemoryPriority(pri),
            )
            m.activate()
            memories.append(m)
        return memories


class TestMemoryFilterEngine:
    def setup_method(self) -> None:
        self.engine = MemoryFilterEngine()

    def test_filter_by_category(self):
        memories = [
            self._make_memory(cat=MemoryCategory.FACT),
            self._make_memory(cat=MemoryCategory.PREFERENCE),
        ]
        filtered = self.engine.apply(memories, MemoryFilter(category="profile"))
        assert len(filtered) == 0

        filtered = self.engine.apply(memories, MemoryFilter(category="fact"))
        assert len(filtered) == 1

    def test_filter_active_only(self):
        memories = [self._make_memory(), self._make_memory()]
        memories[1].activate()
        memories[1].archive()
        filtered = self.engine.apply(memories, MemoryFilter(active_only=True))
        assert len(filtered) >= 1

    def test_filter_by_tags(self):
        m1 = self._make_memory(tags=["important", "follow-up"])
        m2 = self._make_memory(tags=["spam"])
        filtered = self.engine.apply([m1, m2], MemoryFilter(tags=["important"]))
        assert len(filtered) == 1

    def test_filter_by_query(self):
        m1 = self._make_memory(value="User likes dark mode")
        m2 = self._make_memory(value="User prefers light mode")
        filtered = self.engine.apply([m1, m2], MemoryFilter(query="dark"))
        assert len(filtered) == 1
        assert "dark" in filtered[0].value

    def test_filter_by_scope(self):
        memories = [
            self._make_memory(scope=MemoryScope.USER),
            self._make_memory(scope=MemoryScope.CONVERSATION),
        ]
        filtered = self.engine.apply(memories, MemoryFilter(scope="user"))
        assert len(filtered) == 1

    def test_filter_by_status(self):
        m1 = self._make_memory()
        m2 = self._make_memory()
        m2.activate()
        m2.archive()
        filtered = self.engine.apply([m1, m2], MemoryFilter(status="archived"))
        assert len(filtered) == 1

    def test_filter_no_criteria(self):
        memories = [self._make_memory(), self._make_memory()]
        filtered = self.engine.apply(memories)
        assert len(filtered) == 2

    def test_filter_empty_list(self):
        assert self.engine.apply([]) == []

    @staticmethod
    def _make_memory(cat=MemoryCategory.FACT, scope=MemoryScope.USER,
                     tags=None, value="test") -> Memory:
        m = Memory(
            user_id="u1",
            value=value,
            category=cat,
            scope=scope,
            tags=tags or [],
        )
        m.activate()
        return m


class TestMemorySelectionEngine:
    def setup_method(self) -> None:
        self.engine = MemorySelectionEngine()

    def test_select_top(self):
        memories = self._make_memories()
        top = self.engine.select_top(memories, 2)
        assert len(top) == 2

    def test_select_by_importance(self):
        memories = self._make_memories()
        selected = self.engine.select_by_importance(memories, MemoryImportance.HIGH)
        for m in selected:
            assert IMPORTANCE_ORDER[m.importance.value] <= IMPORTANCE_ORDER["high"]

    def test_select_by_confidence(self):
        memories = self._make_memories()
        selected = self.engine.select_by_confidence(memories, MemoryConfidence.HIGH)
        for m in selected:
            assert CONFIDENCE_ORDER[m.confidence.value] <= CONFIDENCE_ORDER["high"]

    @staticmethod
    def _make_memories() -> list[Memory]:
        memories = []
        for i in range(5):
            m = Memory(user_id="u1", value=f"test_{i}")
            m.activate()
            memories.append(m)
        return memories


class TestMemoryResult:
    def test_has_more(self):
        result = MemoryResult(items=[], total=100, skip=0, limit=20)
        assert result.has_more

        result = MemoryResult(items=[], total=10, skip=0, limit=20)
        assert not result.has_more

    def test_page_count(self):
        result = MemoryResult(items=[], total=100, limit=20)
        assert result.page_count == 5

        result = MemoryResult(items=[], total=101, limit=20)
        assert result.page_count == 6

        result = MemoryResult(items=[], total=0, limit=0)
        assert result.page_count == 0

    def test_to_dict(self):
        result = MemoryResult(items=[], total=50, skip=0, limit=20)
        d = result.to_dict()
        assert d["total"] == 50
        assert d["has_more"] is True
        assert d["count"] == 0


class TestMemoryPage:
    def test_next_skip(self):
        page = MemoryPage(skip=0, limit=20)
        assert page.next_skip == 20

        page = MemoryPage(skip=20, limit=10)
        assert page.next_skip == 30


class TestMemoryFilter:
    def test_to_repo_kwargs(self):
        filter_obj = MemoryFilter(user_id="u1", category="fact", active_only=True)
        kwargs = filter_obj.to_repo_kwargs()
        assert kwargs["user_id"] == "u1"
        assert kwargs["category"] == "fact"
        assert "active_only" not in kwargs


class TestMemorySort:
    def test_sort_by_mapping(self):
        assert MemorySort(field=MemorySortField.IMPORTANCE).sort_by == "importance"
        assert MemorySort(field=MemorySortField.RECENCY).sort_by == "last_activity_at"
        assert MemorySort(field=MemorySortField.CREATED_AT).sort_by == "created_at"

    def test_sort_desc(self):
        assert MemorySort(field=MemorySortField.IMPORTANCE, order=MemorySortOrder.DESC).sort_desc is True
        assert MemorySort(field=MemorySortField.IMPORTANCE, order=MemorySortOrder.ASC).sort_desc is False


class TestMemoryQueryEngine:
    def setup_method(self) -> None:
        self.engine = MemoryQueryEngine()

    def test_execute_basic(self):
        memories = self._make_memories(10)
        result = self.engine.execute(memories)
        assert result.total == 10
        assert len(result.items) == 10

    def test_execute_with_pagination(self):
        memories = self._make_memories(50)
        result = self.engine.execute(memories, page=MemoryPage(skip=0, limit=10))
        assert result.total == 50
        assert len(result.items) == 10
        assert result.has_more

    def test_execute_with_filter(self):
        m1 = self._make_memory(value="alpha")
        m2 = self._make_memory(value="beta")
        result = self.engine.execute([m1, m2], filter_obj=MemoryFilter(query="alpha"))
        assert result.total == 1
        assert result.items[0].value == "alpha"

    def test_execute_with_sort(self):
        memories = [
            self._make_memory(imp=MemoryImportance.LOW),
            self._make_memory(imp=MemoryImportance.CRITICAL),
        ]
        result = self.engine.execute(
            memories,
            sort=MemorySort(field=MemorySortField.IMPORTANCE),
        )
        assert result.items[0].importance == MemoryImportance.CRITICAL

    def test_execute_empty_list(self):
        result = self.engine.execute([])
        assert result.total == 0
        assert len(result.items) == 0

    def test_execute_second_page(self):
        memories = self._make_memories(25)
        result = self.engine.execute(memories, page=MemoryPage(skip=20, limit=10))
        assert result.total == 25
        assert len(result.items) == 5

    @staticmethod
    def _make_memory(imp=MemoryImportance.MEDIUM, value="test") -> Memory:
        m = Memory(user_id="u1", value=value, importance=imp)
        m.activate()
        return m

    @staticmethod
    def _make_memories(count: int) -> list[Memory]:
        return [Memory(user_id="u1", value=f"test_{i}") for i in range(count)]
