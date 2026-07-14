import json
import logging
import unittest
from io import StringIO
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from tutor_agent.observability import PIIRedactor, StructuredJsonFormatter, trace_action

class TestObservability(unittest.TestCase):

    def test_pii_redactor(self):
        # Email Redaction
        self.assertEqual(
            PIIRedactor.redact("Contact me at test.user@example.com for info."),
            "Contact me at [REDACTED_EMAIL] for info."
        )
        
        # Phone Number Redaction
        self.assertEqual(
            PIIRedactor.redact("Call me at 123-456-7890 immediately."),
            "Call me at [REDACTED_PHONE] immediately."
        )
        
        # SSN Redaction
        self.assertEqual(
            PIIRedactor.redact("My SSN is 123-45-6789."),
            "My SSN is [REDACTED_SSN]."
        )
        
        # Credit Card Redaction
        self.assertEqual(
            PIIRedactor.redact("Card number 1234-5678-1234-5678."),
            "Card number [REDACTED_CARD]."
        )

    def test_structured_json_formatter(self):
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredJsonFormatter())
        
        logger = logging.getLogger("test_structured_json")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Act
        logger.info("User requested billing help for test@example.com", extra={"intent": "Billing inquiry"})
        
        # Assert
        log_output = log_stream.getvalue().strip()
        log_json = json.loads(log_output)
        
        self.assertEqual(log_json["level"], "INFO")
        self.assertEqual(log_json["logger"], "test_structured_json")
        self.assertEqual(log_json["intent"], "Billing inquiry")
        # Ensure PII was redacted from log message
        self.assertEqual(log_json["message"], "User requested billing help for [REDACTED_EMAIL]")

    def test_intent_vs_outcome_tracking(self):
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredJsonFormatter())
        
        logger = logging.getLogger("tutor_agent")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Act
        intent = "Generate dynamic curriculum"
        with trace_action("generate_curriculum", intent=intent, extra_attrs={"topic": "Python"}) as tracer:
            tracer.set_outcome("Curriculum created with 3 subjects", success=True)
            
        # Assert
        log_lines = log_stream.getvalue().strip().split("\n")
        self.assertTrue(len(log_lines) >= 2)
        
        # Start Log check
        start_log = json.loads(log_lines[0])
        self.assertEqual(start_log["message"], "Starting action: generate_curriculum")
        self.assertEqual(start_log["intent"], intent)
        
        # Outcome Log check
        outcome_log = json.loads(log_lines[1])
        self.assertEqual(outcome_log["message"], "Action 'generate_curriculum' succeeded: Curriculum created with 3 subjects")
        self.assertEqual(outcome_log["intent"], intent)
        self.assertEqual(outcome_log["outcome"], "Curriculum created with 3 subjects")
