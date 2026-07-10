"""
PII 脱敏模块单元测试
纯逻辑测试，不需要 mock 任何外部依赖
"""

from app.core.pii_anonymizer import PIIAnonymizer, create_default_anonymizer


class TestPIIEmail:
    """邮箱脱敏测试"""

    def test_mask_email(self):
        anonymizer = create_default_anonymizer()
        result = anonymizer.anonymize("联系我 test@example.com 谢谢")
        assert "test@example.com" not in result
        assert "te***@example.com" in result

    def test_mask_multiple_emails(self):
        anonymizer = create_default_anonymizer()
        result = anonymizer.anonymize("a@b.com 和 c@d.com")
        assert "a@b.com" not in result
        assert "c@d.com" not in result


class TestPIICreditCard:
    """信用卡脱敏测试"""

    def test_mask_credit_card_with_dashes(self):
        anonymizer = create_default_anonymizer()
        result = anonymizer.anonymize("卡号 4111-1111-1111-1234")
        assert "4111-1111-1111" not in result
        assert "1234" in result  # 保留后4位

    def test_mask_credit_card_no_separator(self):
        anonymizer = create_default_anonymizer()
        result = anonymizer.anonymize("卡号 4111111111111234")
        assert "4111111111111234" not in result


class TestPIIPhone:
    """手机号脱敏测试"""

    def test_mask_cn_phone(self):
        anonymizer = create_default_anonymizer()
        result = anonymizer.anonymize("电话 13812345678")
        assert "13812345678" not in result
        assert "138****5678" in result


class TestPIINoPII:
    """无 PII 场景"""

    def test_no_pii_unchanged(self):
        anonymizer = create_default_anonymizer()
        text = "这是一段普通文本，没有敏感信息。"
        result = anonymizer.anonymize(text)
        assert result == text

    def test_empty_string(self):
        anonymizer = create_default_anonymizer()
        assert anonymizer.anonymize("") == ""


class TestPIIMultiple:
    """多类型 PII 同时存在"""

    def test_mixed_pii(self):
        anonymizer = create_default_anonymizer()
        text = "邮箱 test@example.com，手机 13812345678"
        result = anonymizer.anonymize(text)
        assert "test@example.com" not in result
        assert "13812345678" not in result


class TestPIIStrategies:
    """不同脱敏策略测试"""

    def test_redact_strategy(self):
        anonymizer = PIIAnonymizer()
        anonymizer.add_pattern("email", strategy="redact")
        result = anonymizer.anonymize("联系 test@example.com")
        assert "[REDACTED_EMAIL]" in result

    def test_hash_strategy(self):
        anonymizer = PIIAnonymizer()
        anonymizer.add_pattern("email", strategy="hash")
        result = anonymizer.anonymize("联系 test@example.com")
        assert "[HASH_EMAIL_" in result

    def test_mask_strategy(self):
        anonymizer = PIIAnonymizer()
        anonymizer.add_pattern("email", strategy="mask")
        result = anonymizer.anonymize("联系 test@example.com")
        assert "te***@example.com" in result


class TestPIIDetect:
    """PII 检测测试"""

    def test_detect_email(self):
        anonymizer = create_default_anonymizer()
        matches = anonymizer.detect("联系 test@example.com")
        assert len(matches) == 1
        assert matches[0].pii_type == "email"
        assert matches[0].text == "test@example.com"

    def test_detect_multiple(self):
        anonymizer = create_default_anonymizer()
        matches = anonymizer.detect("邮箱 test@example.com 手机 13812345678")
        assert len(matches) == 2
