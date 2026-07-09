from application.response_validation.models import ResponseMetadata, ValidationReport, ValidationResult


class TestValidationModels:
    def test_validation_result_defaults(self):
        r = ValidationResult(passed=True)
        assert r.passed
        assert r.errors == []
        assert r.warnings == []
        assert r.details == {}

    def test_validation_result_failed(self):
        r = ValidationResult(passed=False, errors=["too short"])
        assert not r.passed
        assert "too short" in r.errors

    def test_validation_result_merge_both_passed(self):
        a = ValidationResult(passed=True)
        b = ValidationResult(passed=True)
        c = a.merge(b)
        assert c.passed

    def test_validation_result_merge_one_failed(self):
        a = ValidationResult(passed=True)
        b = ValidationResult(passed=False, errors=["error"])
        c = a.merge(b)
        assert not c.passed
        assert "error" in c.errors

    def test_validation_report_defaults(self):
        report = ValidationReport(passed=True)
        assert report.passed
        assert report.results == {}
        assert report.total_checks == 0
        assert report.passed_checks == 0
        assert report.failed_checks == 0
        assert report.latency_ms == 0.0

    def test_validation_report_all_errors(self):
        report = ValidationReport(
            passed=False,
            results={
                "rule1": ValidationResult(passed=False, errors=["err1"]),
                "rule2": ValidationResult(passed=False, errors=["err2"]),
            },
            total_checks=2,
            passed_checks=0,
            failed_checks=2,
        )
        errors = report.all_errors
        assert len(errors) == 2
        assert any("[rule1]" in e for e in errors)

    def test_validation_report_all_warnings(self):
        report = ValidationReport(
            passed=True,
            results={
                "rule1": ValidationResult(passed=True, warnings=["warn1"]),
            },
        )
        warnings = report.all_warnings
        assert len(warnings) == 1
        assert "[rule1]" in warnings[0]

    def test_response_metadata_defaults(self):
        meta = ResponseMetadata(content="hello")
        assert meta.content == "hello"
        assert meta.content_type == "text"
        assert meta.content_length == 0
        assert not meta.has_json
        assert not meta.has_markdown
        assert meta.detected_pii == []
