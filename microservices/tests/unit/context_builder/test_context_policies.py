from application.context_builder.policies import (
    ContextPolicy,
    LayerOrderingPolicy,
    OrderingDirection,
    PrivacyPolicy,
    VisibilityPolicy,
)


class TestLayerOrderingPolicy:
    def test_sort_layers_default(self):
        policy = LayerOrderingPolicy()
        result = policy.sort_layers(["memory", "system", "identity"])
        assert result == sorted(["memory", "system", "identity"])

    def test_sort_layers_custom_order(self):
        policy = LayerOrderingPolicy(order=["system", "identity", "memory"])
        result = policy.sort_layers(["memory", "system", "identity"])
        assert result == ["system", "identity", "memory"]

    def test_sort_layers_with_extra(self):
        policy = LayerOrderingPolicy(order=["system", "memory"])
        result = policy.sort_layers(["unknown", "memory", "system"])
        assert result[0] == "system"
        assert result[1] == "memory"

    def test_descending_order(self):
        policy = LayerOrderingPolicy(
            order=["system", "identity", "memory"],
            direction=OrderingDirection.DESCENDING,
        )
        result = policy.sort_layers(["memory", "system", "identity"])
        assert result == ["memory", "identity", "system"]


class TestVisibilityPolicy:
    def test_no_filter_when_none(self):
        policy = VisibilityPolicy()
        layers = {"system": {}, "memory": {}}
        assert policy.filter(layers) == layers

    def test_filters_allowed(self):
        policy = VisibilityPolicy(allowed_layers=["system"])
        assert policy.filter({"system": {}, "memory": {}}) == {"system": {}}


class TestPrivacyPolicy:
    def test_redact_sensitive(self):
        policy = PrivacyPolicy(sensitive_fields=["email"])
        result = policy.redact({"email": "test@example.com", "name": "John"})
        assert result["email"] == "te****om"
        assert result["name"] == "John"

    def test_redact_nested(self):
        policy = PrivacyPolicy(sensitive_fields=["phone"])
        result = policy.redact({"user": {"phone": "1234567890", "name": "John"}})
        assert result["user"]["phone"] == "12****90"
        assert result["user"]["name"] == "John"

    def test_redact_short_value(self):
        policy = PrivacyPolicy(sensitive_fields=["key"])
        result = policy.redact({"key": "ab"})
        assert result["key"] == "****"


class TestContextPolicy:
    def test_defaults(self):
        policy = ContextPolicy()
        assert policy.max_layers == 10
        assert not policy.fail_on_missing_source
