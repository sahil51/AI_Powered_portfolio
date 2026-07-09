from application.response_validation.metrics import ResponseMetrics


class TestResponseMetrics:
    def test_defaults(self):
        m = ResponseMetrics()
        assert m.total_validations == 0
        assert m.avg_latency_ms == 0.0
        assert m.pass_rate == 1.0

    def test_record_passed_validation(self):
        m = ResponseMetrics()
        m.record_validation(passed=True, latency_ms=10.0)
        assert m.total_validations == 1
        assert m.passed_validations == 1
        assert m.failed_validations == 0
        assert m.avg_latency_ms == 10.0
        assert m.pass_rate == 1.0

    def test_record_failed_validation(self):
        m = ResponseMetrics()
        m.record_validation(passed=False, latency_ms=5.0)
        assert m.failed_validations == 1
        assert m.pass_rate == 0.0

    def test_record_with_rule_results(self):
        m = ResponseMetrics()
        m.record_validation(passed=False, latency_ms=10.0, rule_results={"empty": False, "length": True})
        assert m.rule_failures["empty"] == 1
        assert "length" not in m.rule_failures

    def test_record_detections(self):
        m = ResponseMetrics()
        m.record_pii_detection()
        m.record_leakage_detection()
        m.record_sensitive_data_detection()
        assert m.pii_detections == 1
        assert m.leakage_detections == 1
        assert m.sensitive_data_detections == 1

    def test_merge(self):
        a = ResponseMetrics()
        a.record_validation(passed=True, latency_ms=10.0)
        a.record_pii_detection()

        b = ResponseMetrics()
        b.record_validation(passed=False, latency_ms=20.0)
        b.record_leakage_detection()

        a.merge(b)
        assert a.total_validations == 2
        assert a.passed_validations == 1
        assert a.failed_validations == 1
        assert a.pii_detections == 1
        assert a.leakage_detections == 1
