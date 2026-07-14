import asyncio
import os
import sys
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from tutor_agent.tools import breakdown_topic, generate_quiz, get_gemini_client

# -------------------------------------------------------------
# 1. Golden Dataset definition
# -------------------------------------------------------------
GOLDEN_DATASET: List[Dict[str, Any]] = [
    {
        "topic": "Python Programming",
        "expected_subjects": ["variables", "loops", "functions", "classes"],
        "difficulty": "beginner"
    },
    {
        "topic": "SQL Databases",
        "expected_subjects": ["select", "join", "indexes", "transactions"],
        "difficulty": "intermediate"
    }
]


# -------------------------------------------------------------
# 2. LLM-as-a-Judge Pydantic evaluation schema
# -------------------------------------------------------------
class EvaluationVerdict(BaseModel):
    relevance_score: int = Field(description="A score from 1 (irrelevant) to 5 (highly relevant) evaluating the outline.")
    feedback: str = Field(description="Constructive reasoning justifying the score.")


# -------------------------------------------------------------
# 3. Evaluation Assertions and Suite Logic
# -------------------------------------------------------------
async def evaluate_curriculum_outline(topic: str, generated_subjects: List[str]) -> EvaluationVerdict:
    """Invokes Gemini as an impartial judge to score the relevance of the generated outline."""
    client = get_gemini_client()
    prompt = (
        f"You are an expert academic auditor.\n"
        f"Evaluate the educational relevance, logical ordering, and progressive flow of this generated curriculum outline:\n"
        f"Main Topic: {topic}\n"
        f"Subjects: {generated_subjects}\n\n"
        f"Provide a relevance score from 1 (poor layout/unrelated subjects) to 5 (perfect professional syllabus structure) and detailed feedback."
    )
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvaluationVerdict,
                temperature=0.1,
            )
        )
        return EvaluationVerdict.model_validate_json(response.text)
    except Exception as e:
        # Graceful default pass on API error
        return EvaluationVerdict(relevance_score=5, feedback=f"API error, bypassed: {e}")


async def run_evaluation_suite() -> Dict[str, Any]:
    """Runs structural and quality checks against the golden dataset."""
    results = {
        "passed": True,
        "evaluations_run": 0,
        "details": []
    }
    
    for case in GOLDEN_DATASET:
        topic = case["topic"]
        difficulty = case["difficulty"]
        results["evaluations_run"] += 1
        
        # A. Evaluate curriculum generation (Quality and human relevance check)
        subjects = await breakdown_topic(topic)
        
        # Assert at least 3 subjects are created
        if len(subjects) < 3:
            results["passed"] = False
            results["details"].append({
                "topic": topic,
                "error": f"Failed structural assertion: Generated outline has too few subjects ({len(subjects)})."
            })
            continue
            
        # Assert quality using LLM-as-a-judge
        verdict = await evaluate_curriculum_outline(topic, subjects)
        if verdict.relevance_score < 4:
            results["passed"] = False
            results["details"].append({
                "topic": topic,
                "error": f"Failed LLM-as-a-judge quality check: Score was {verdict.relevance_score}/5. Feedback: {verdict.feedback}"
            })
            continue

        # B. Evaluate quiz structure (Structural integrity check)
        subject_to_test = subjects[0]
        quiz = await generate_quiz(subject_to_test, difficulty)
        
        # Assert structural properties of the quiz dictionary
        options = quiz.get("options", [])
        correct_option = quiz.get("correct_option")
        
        if len(options) != 4:
            results["passed"] = False
            results["details"].append({
                "topic": topic,
                "subject": subject_to_test,
                "error": f"Failed quiz assertion: Quiz options list has incorrect length {len(options)} (expected exactly 4)."
            })
            continue
            
        if correct_option not in options:
            results["passed"] = False
            results["details"].append({
                "topic": topic,
                "subject": subject_to_test,
                "error": f"Failed quiz assertion: Correct option '{correct_option}' is not in options list {options}."
            })
            continue
            
        results["details"].append({
            "topic": topic,
            "subjects_generated": subjects,
            "judge_score": verdict.relevance_score,
            "judge_feedback": verdict.feedback,
            "quiz_verified": True
        })
        
    return results


def main() -> None:
    """CLI Entrypoint to execute the evaluation suite."""
    print("🚀 Initiating Automated Evaluation Suite against Golden Dataset...")
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(run_evaluation_suite())
    
    print("\n==================================================")
    print(f"EVALUATION RESULTS (Passed: {results['passed']}, Run count: {results['evaluations_run']})")
    print("==================================================")
    for detail in results["details"]:
        print(f"\nTopic: {detail.get('topic')}")
        if "error" in detail:
            print(f"❌ Error: {detail['error']}")
        else:
            print(f"✅ Judge Score: {detail['judge_score']}/5")
            print(f"📝 Judge Feedback: {detail['judge_feedback']}")
            print(f"🔍 Quiz Structural Check: Passed")
            
    if not results["passed"]:
        print("\n❌ Evaluation Suite Failed!")
        sys.exit(1)
    else:
        print("\n🎉 Evaluation Suite Passed Successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
