from application.context_builder.budget import ContextBudget, ContextBudgetPolicy


class TestContextBudget:
    def test_defaults(self):
        budget = ContextBudget()
        assert budget.max_tokens == 8192
        assert budget.reserved_tokens == 1024
        assert budget.available_tokens == 8192 - 1024 - 2048

    def test_total_budget(self):
        budget = ContextBudget(max_tokens=10000, reserved_tokens=1000)
        assert budget.total_budget == 9000


class TestContextBudgetPolicy:
    def test_create_budget(self):
        policy = ContextBudgetPolicy(max_tokens=10000, reserved_tokens=1000, output_tokens=2000)
        weights = {"system": 0.5, "memory": 0.5}
        budget = policy.create_budget(weights)
        assert budget.max_tokens == 10000
        assert budget.reserved_tokens == 1000
        assert budget.output_tokens == 2000
        available = 10000 - 1000 - 2000
        assert budget.layer_allocations["system"] == int(0.5 * available)
        assert budget.layer_allocations["memory"] == int(0.5 * available)

    def test_is_within_budget(self):
        policy = ContextBudgetPolicy()
        budget = ContextBudget(layer_allocations={"system": 1000})
        assert policy.is_within_budget(budget, "system", 500)
        assert policy.is_within_budget(budget, "other", 500)

    def test_enforce(self):
        policy = ContextBudgetPolicy()
        budget = ContextBudget(max_tokens=100, used_tokens=200)
        enforced = policy.enforce(budget)
        assert enforced.compression_enabled
