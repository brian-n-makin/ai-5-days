import json
import logging
import os
import re
from typing import Any, Dict, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# -------------------------------------------------------------
# 1. PII Redactor Utility
# -------------------------------------------------------------
class PIIRedactor:
    """Detects and redacts Personally Identifiable Information (PII) from text."""
    
    # Regular expressions for common PII
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    @classmethod
    def redact(cls, text: str) -> str:
        """Sanitizes text by replacing detected PII patterns with '[REDACTED]'."""
        if not text or not isinstance(text, str):
            return text
        
        text = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = cls.SSN_REGEX.sub("[REDACTED_SSN]", text)
        text = cls.CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)
        return text


# -------------------------------------------------------------
# 2. Structured JSON Log Formatter
# -------------------------------------------------------------
class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter to output structured logs in JSON format with PII redaction."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": PIIRedactor.redact(record.getMessage()),
        }
        
        # Capture context fields / extra attributes
        if hasattr(record, "intent"):
            log_payload["intent"] = record.intent
        if hasattr(record, "outcome"):
            log_payload["outcome"] = record.outcome
            
        # Capture standard exception details if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_payload)


# -------------------------------------------------------------
# 3. Telemetry and Tracing Bootstrapper
# -------------------------------------------------------------
def setup_telemetry() -> None:
    """Configures structured JSON logging and OpenTelemetry request-level tracing."""
    # A. Configure Logging
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    root_logger = logging.getLogger()
    
    # Reset existing handlers to prevent duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    formatter = StructuredJsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    logger = logging.getLogger("tutor_agent")
    logger.propagate = True
    logger.info("Structured JSON Logging initialized successfully.")

    # B. Configure OpenTelemetry Tracing
    try:
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            provider = TracerProvider()
            
            # Print traces to console if TRACE_TO_CONSOLE is enabled
            if os.environ.get("TRACE_TO_CONSOLE") == "true":
                processor = SimpleSpanProcessor(ConsoleSpanExporter())
                provider.add_span_processor(processor)
                
            trace.set_tracer_provider(provider)
            logger.info("OpenTelemetry TracerProvider registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to register OpenTelemetry TracerProvider: {e}")


def get_tracer() -> trace.Tracer:
    """Retrieves the OpenTelemetry Tracer instance."""
    return trace.get_tracer("tutor_agent")


def trace_action(span_name: str, intent: str, extra_attrs: Optional[Dict[str, Any]] = None):
    """Context manager / decorator factory helper to log Intent vs. Outcome and redact PII inside traces."""
    class TracedActionContext:
        def __init__(self):
            self.tracer = get_tracer()
            self.logger = logging.getLogger("tutor_agent")
            self.span = None

        def __enter__(self):
            self.span = self.tracer.start_span(span_name)
            self.span.set_attribute("app.intent", PIIRedactor.redact(intent))
            if extra_attrs:
                for k, v in extra_attrs.items():
                    self.span.set_attribute(f"app.{k}", PIIRedactor.redact(str(v)))
            
            self.logger.info(f"Starting action: {span_name}", extra={"intent": intent})
            return self

        def set_outcome(self, outcome: str, success: bool = True, details: Optional[str] = None):
            if self.span:
                redacted_outcome = PIIRedactor.redact(outcome)
                self.span.set_attribute("app.outcome", redacted_outcome)
                self.span.set_attribute("app.success", success)
                if details:
                    self.span.set_attribute("app.details", PIIRedactor.redact(details))
                
                log_extra = {"intent": intent, "outcome": outcome}
                if success:
                    self.logger.info(f"Action '{span_name}' succeeded: {outcome}", extra=log_extra)
                else:
                    self.logger.error(f"Action '{span_name}' failed: {outcome}", extra=log_extra)

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self.set_outcome(f"Exception raised: {exc_val}", success=False)
                if self.span:
                    self.span.record_exception(exc_val)
                    self.span.set_status(trace.Status(trace.StatusCode.ERROR))
            if self.span:
                self.span.end()
            return False

    return TracedActionContext()
