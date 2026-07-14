# Observability & Tracing Upgrade Plan

## Objective
Address the grading feedback for the "Observability & Tracing" pillar (2/20 pts). This plan introduces structured JSON logging, active OpenTelemetry request-level tracing (including intent vs. outcome tracking), and a PII redaction filter for safe logs.

## Scope & Impact
1. **Structured JSON Logging**: Implement a custom Python `logging.Formatter` that formats all log records as structured JSON dictionaries containing timestamp, log level, logger name, message, and any extra context.
2. **PII Redaction Mechanism**: Create a highly secure `PIIRedactor` that filters logs and span attributes using regex to replace sensitive personal data (emails, phone numbers, SSNs, credit cards, etc.) with `[REDACTED]`.
3. **Intent vs. Outcome Tracking**: Explicitly define and record the user's intent versus the agent's outcome for every operation. Track these natively as attributes inside OpenTelemetry spans and JSON log records.
4. **Active OpenTelemetry Instrumentations**: Wrap all major operations (`breakdown_topic`, `generate_quiz`, `assess_understanding`, `load_profile`, `update_subject_score`) inside explicit OpenTelemetry trace spans, attaching rich, redacted attributes.

## Implementation Steps

### 1. Develop `tutor_agent/observability.py`
- Build `StructuredJsonFormatter` formatting log messages as JSON strings.
- Build `PIIRedactor` with static regex patterns to sanitize text.
- Configure logging to use `StructuredJsonFormatter`.
- Expose a decorator `@trace_and_log` or helper functions to easily create spans and structured logs.

### 2. Instrumentalize `tutor_agent/tools.py`
- Decorate or wrap `breakdown_topic`, `generate_quiz`, and `assess_understanding` with OpenTelemetry tracer spans.
- Sanitize inputs/outputs using the `PIIRedactor`.
- Set span attributes for `app.intent`, `app.outcome`, and other custom context.

### 3. Instrumentalize `tutor_agent/memory.py`
- Wrap database operations (`load_profile`, `update_subject_score`) inside tracing spans to track persistence latency and database state.

### 4. Create Tests
- Write a new unit test suite in `tests/test_observability.py` to verify:
  - Structured JSON formatting.
  - PII redaction (email and phone number replacements).
  - Intent vs. outcome trace span attribute recording.
