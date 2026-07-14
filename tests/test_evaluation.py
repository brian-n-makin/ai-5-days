import sys
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from tutor_agent.eval_suite import run_evaluation_suite, evaluate_curriculum_outline

class TestEvaluationSuite(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Prevent prompt hangs on sys.stdin inside eval tools
        self.isatty_patcher = patch.object(sys.stdin, "isatty", return_value=False)
        self.mock_isatty = self.isatty_patcher.start()

    def tearDown(self):
        self.isatty_patcher.stop()

    @patch("tutor_agent.eval_suite.breakdown_topic")
    @patch("tutor_agent.eval_suite.generate_quiz")
    @patch("tutor_agent.eval_suite.evaluate_curriculum_outline")
    async def test_evaluation_suite_pass_condition(self, mock_judge, mock_generate_quiz, mock_breakdown):
        # Mocking the sub-agents and tools to return standard valid results
        mock_breakdown.return_value = ["Topic 1", "Topic 2", "Topic 3"]
        mock_generate_quiz.return_value = {
            "question": "What is Python?",
            "options": ["A", "B", "C", "D"],
            "correct_option": "A",
            "explanation": "High-level language."
        }
        
        # Mocking the judge to give a passing score
        mock_judge_verdict = MagicMock()
        mock_judge_verdict.relevance_score = 5
        mock_judge_verdict.feedback = "Outstanding layout."
        mock_judge.return_value = mock_judge_verdict
        
        # Act
        results = await run_evaluation_suite()
        
        # Assert
        self.assertTrue(results["passed"])
        self.assertEqual(results["evaluations_run"], 2)
        self.assertEqual(len(results["details"]), 2)
        self.assertTrue(results["details"][0]["quiz_verified"])
        self.assertEqual(results["details"][0]["judge_score"], 5)

    @patch("tutor_agent.eval_suite.breakdown_topic")
    @patch("tutor_agent.eval_suite.generate_quiz")
    @patch("tutor_agent.eval_suite.evaluate_curriculum_outline")
    async def test_evaluation_suite_fail_condition_too_few_subjects(self, mock_judge, mock_generate_quiz, mock_breakdown):
        # Setup mock to return too few subjects
        mock_breakdown.return_value = ["Only One Subject"]
        
        results = await run_evaluation_suite()
        
        self.assertFalse(results["passed"])
        self.assertIn("too few subjects", results["details"][0]["error"])

    @patch("tutor_agent.eval_suite.breakdown_topic")
    @patch("tutor_agent.eval_suite.generate_quiz")
    @patch("tutor_agent.eval_suite.evaluate_curriculum_outline")
    async def test_evaluation_suite_fail_condition_poor_judge_score(self, mock_judge, mock_generate_quiz, mock_breakdown):
        mock_breakdown.return_value = ["Topic 1", "Topic 2", "Topic 3"]
        
        mock_judge_verdict = MagicMock()
        mock_judge_verdict.relevance_score = 2
        mock_judge_verdict.feedback = "Poor, illogical ordering."
        mock_judge.return_value = mock_judge_verdict
        
        results = await run_evaluation_suite()
        
        self.assertFalse(results["passed"])
        self.assertIn("quality check", results["details"][0]["error"])
