# Tool & Interface Upgrade Plan

## Objective
Address the grading feedback for the "Tool & Interface Design" pillar (10/20 pts). This plan updates tool docstrings to include comprehensive Google-style parameter descriptions and refactors error handling to return structured recovery instructions for the LLM rather than silent, hardcoded fallbacks.

## Scope & Impact
1. **Detailed Google-Style Docstrings**: Add comprehensive `Args:`, `Returns:`, and `Raises:` sections to every single registered tool function. This ensures the LLM completely understands parameter expectations during function-calling.
2. **LLM Adaptive Recovery Instructions**: Eliminate hardcoded fallbacks in `breakdown_topic` and `generate_quiz`. Instead of returning static data on exceptions, raise highly informative, structured errors containing explicit step-by-step instructions telling the LLM how to recover dynamically (e.g., teaching manually, adjusting prompt parameters, or asking open-ended questions).

## Implementation Steps

### 1. Refactor `tutor_agent/tools.py`
- Rewrite tool docstrings to rigorously include:
  - Detailed types, scopes, and descriptions for all parameters.
  - Detailed descriptions of return objects and schema structures.
- Modify `breakdown_topic`:
  - On exception, instead of returning a hardcoded list, raise a `ValueError` explaining the failure and instructing the LLM: *"Please recover by asking the student to manually list 3 subjects they would like to learn about the topic, and initialize the learning session using those."*
- Modify `generate_quiz`:
  - On exception, instead of a hardcoded fallback quiz, raise a `ValueError` instructing the LLM: *"Please recover by dynamically generating a direct, open-ended conceptual question about the subject yourself, asking the student for an explanation, and manually evaluating their response."*

### 2. Update Tests (`tests/test_tools.py` & `tests/test_evaluation.py`)
- Update mock assertions to expect these exceptions and verify that the raised exceptions contain the correct recovery instructions.
