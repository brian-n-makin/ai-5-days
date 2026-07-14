# Infrastructure & CI/CD Upgrade Plan

## Objective
Address the grading feedback for the "Infrastructure & CI/CD" pillar (5/15 pts). This plan introduces an automated LLM-as-a-judge evaluation suite testing against a defined "golden dataset", and adds Terraform Infrastructure as Code (IaC) configurations for secure, scalable cloud deployment.

## Scope & Impact
1. **Automated Evaluation Suite**: Develop a dedicated LLM evaluation system (`tutor_agent/eval_suite.py`) testing the agent against a "golden dataset" of topics. It measures:
   - Curriculum quality (relevance and order) using an LLM-as-a-judge evaluator.
   - Quiz logical structure (exactly 4 options, valid correct option, non-empty explanation).
2. **Infrastructure as Code (IaC)**: Handcraft a suite of Terraform (`.tf`) configurations to provision Google Cloud resources securely:
   - Google Cloud Artifact Registry (to store the docker image).
   - Google Cloud Run (to host the agent as a containerized microservice).
   - Secret Manager (to store and reference `GEMINI_API_KEY` securely without exposure).
   - IAM Roles (to grant Cloud Run permissions to read from Secret Manager).
3. **CI/CD Integration**: Update `.github/workflows/main.yml` to automatically run both the standard unit tests and the newly built evaluation suite on every push.

## Implementation Steps

### 1. Build the Automated Evaluation Suite (`tutor_agent/eval_suite.py` & `tests/test_evaluation.py`)
- Define a "golden dataset" of topics (e.g., Python, Kubernetes, Machine Learning) and expected curriculum/quiz structures.
- Implement `run_evaluations()` doing non-blocking LLM calls.
- Integrate an LLM-as-a-judge prompt to rate generated outlines on a scale of 1-5, asserting quality `>= 4`.
- Write `tests/test_evaluation.py` wrapping these assertions.

### 2. Create Infrastructure as Code (`terraform/` directory)
- `terraform/main.tf`: Define providers (`google`), Google Artifact Registry, Secret Manager, Cloud Run service, and IAM roles.
- `terraform/variables.tf`: Declare variables (`project_id`, `region`).
- `terraform/outputs.tf`: Output the Artifact Registry repository URL and Cloud Run Service URL.

### 3. Update CI/CD Workflow (`.github/workflows/main.yml`)
- Update the workflow to execute the evaluation suite automatically in the runner pipeline.
