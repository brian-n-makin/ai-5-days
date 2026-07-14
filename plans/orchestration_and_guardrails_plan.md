# Orchestration & Logic Upgrade Plan

## Objective
Address the grading feedback for the "Orchestration & Logic" pillar (0/20 pts). This plan introduces a multi-agent collaboration pattern, model-strategic routing, self-evaluation guardrails, and human-in-the-loop confirmation hooks.

## Scope & Impact
1. **Multi-Agent Pattern**: Deconstruct the monolithic tutor into a hierarchical team of 3 collaborating ADK agents:
   - `CurriculumPlannerAgent`: Manages syllabus breakdown and progression.
   - `TutorAgent`: Dedicated to interactive teaching, explaining, and answering questions.
   - `EvaluationQuizAgent`: Focuses on quizzing, evaluation, and grading.
   - Unified Router: A root `TutorSystem` agent that orchestrates transfers.
2. **Strategic Model Routing**: Assign different models based on task complexity (e.g., lightweight `gemini-3-flash` for the structured planner, and the highly advanced `gemini-3.5-flash` for teaching and quizzing).
3. **Self-Evaluation & Security Guardrails**: Implement an automated self-evaluation step during quiz generation where a secondary LLM validator audits the quiz for correctness, accuracy, and safety before presenting it.
4. **Human-in-the-Loop Confirmation**: Integrate user confirmation hooks before critical state-mutating tools execute (e.g., confirming the generated curriculum outline and confirming mastery score updates).

## Implementation Steps

### 1. Refactor `tutor_agent/tools.py`
- Add **Human-in-the-Loop Confirmation**:
  - In `breakdown_topic`, prompt the user to review and confirm the generated subjects before saving.
  - In `assess_understanding`, prompt the user to confirm the mastery score adjustment.
- Add **Self-Evaluation Guardrail**:
  - In `generate_quiz`, after receiving a generated question, call a separate prompt validator to evaluate the question and options for correctness and safety. If invalid, regenerate.

### 2. Refactor `tutor_agent/orchestrator.py`
- Define instructions for the sub-agents and root agent.
- Create:
  - `CurriculumPlannerAgent` with tools `breakdown_topic` and `get_progress_summary` running on `gemini-3-flash` (or default fast model).
  - `TutorAgent` focused on lessons and clarifications running on `gemini-3.5-flash`.
  - `EvaluationQuizAgent` with tools `generate_quiz` and `assess_understanding` running on `gemini-3.5-flash`.
- Link them using `sub_agents` of a root `TutorSystem` agent to enable automatic peer-to-peer transfers.

### 3. Update tests and CLI
- Ensure `tests/` cover the new multi-agent instantiation.
- Ensure the CLI starts the root `TutorSystem` agent.
