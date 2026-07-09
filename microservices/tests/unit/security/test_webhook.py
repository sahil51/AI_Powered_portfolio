import hashlib
import hmac
import time

import pytest

from security.webhook_verifier import WebhookVerifier


class TestWebhookVerifier:
    @pytest.fixture
    def verifier(self):
        return WebhookVerifier(secret="test-secret")

    def test_verify_hmac_valid(self, verifier):
        payload = '{"event": "test"}'
        signature = hmac.new(
            b"test-secret",
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        result = verifier.verify_hmac_header(payload, signature)
        assert result.verified

    def test_verify_hmac_invalid(self, verifier):
        payload = '{"event": "test"}'
        result = verifier.verify_hmac_header(payload, "invalid-signature")
        assert not result.verified
        assert "mismatch" in result.error

    def test_verify_hmac_empty_payload(self, verifier):
        signature = hmac.new(b"test-secret", b"", hashlib.sha256).hexdigest()
        result = verifier.verify_hmac_header("", signature)
        assert result.verified

    def test_timestamp_validation_valid(self, verifier):
        timestamp = time.time()
        assert verifier.validate_timestamp(timestamp)

    def test_timestamp_validation_old(self, verifier):
        old_timestamp = time.time() - 600
        assert not verifier.validate_timestamp(old_timestamp)

    def test_timestamp_header_valid(self, verifier):
        ts = str(time.time())
        result = verifier.validate_timestamp_header(ts)
        assert result.verified

    def test_timestamp_header_invalid(self, verifier):
        result = verifier.validate_timestamp_header("not-a-number")
        assert not result.verified

    def test_replay_protection(self, verifier):
        key = "idem-123"
        first = verifier.check_replay(key)
        assert first.verified
        second = verifier.check_replay(key)
        assert not second.verified
        assert "Replay" in second.error

    def test_verify_full_success(self, verifier):
        payload = '{"data": "test"}'
        ts = str(time.time())
        idem = "unique-key-1"
        sig = hmac.new(b"test-secret", payload.encode(), hashlib.sha256).hexdigest()
        result = verifier.verify_full(payload, sig, ts, idem)
        assert result.verified

    def test_verify_full_bad_signature(self, verifier):
        result = verifier.verify_full(
            '{"data": "test"}', "bad-sig", str(time.time()), "key-2",
        )
        assert not result.verified

    def test_verify_full_bad_timestamp(self, verifier):
        payload = '{"data": "test"}'
        sig = hmac.new(b"test-secret", payload.encode(), hashlib.sha256).hexdigest()
        result = verifier.verify_full(payload, sig, "0", "key-3")
        assert not result.verified

    def test_verify_full_replay(self, verifier):
        payload = '{"data": "test"}'
        ts = str(time.time())
        sig = hmac.new(b"test-secret", payload.encode(), hashlib.sha256).hexdigest()
        verifier.verify_full(payload, sig, ts, "replay-key")
        result = verifier.verify_full(payload, sig, ts, "replay-key")
        assert not result.verified

    def test_set_secret(self, verifier):
        verifier.set_secret("new-secret")
        assert verifier.secret == "new-secret"
