import sys
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from tutor_agent.tools import (
    breakdown_topic,
    generate_quiz,
    assess_understanding,
    get_progress_summary,
    Curriculum,
    Quiz
)
from tutor_agent.memory import StudentProfileManager

class TestTools(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Prevent tests from hanging on human-in-the-loop prompts by mocking isatty
        self.isatty_patcher = patch.object(sys.stdin, "isatty", return_value=False)
        self.mock_isatty = self.isatty_patcher.start()

    def tearDown(self):
        self.isatty_patcher.stop()

    @patch("tutor_agent.tools.get_gemini_client")
    @patch("tutor_agent.tools.StudentProfileManager")
    async def test_breakdown_topic(self, mock_manager_cls, mock_get_client):
        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Async mock for aio.models.generate_content
        mock_response = MagicMock()
        mock_response.text = '{"subjects": ["Variables", "Loops", "Functions"]}'
        
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        mock_manager = AsyncMock()
        mock_manager_cls.return_value = mock_manager
        
        # Act
        res = await breakdown_topic("Python")
        
        # Assert
        self.assertEqual(res, ["Variables", "Loops", "Functions"])
        mock_manager.initialize_profile.assert_called_once_with("Python", ["Variables", "Loops", "Functions"])

    @patch("tutor_agent.tools.get_gemini_client")
    @patch("tutor_agent.tools.StudentProfileManager")
    async def test_breakdown_topic_failure_recovery_instructions(self, mock_manager_cls, mock_get_client):
        # Setup mock to trigger exception
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API limit exceeded"))
        
        # Assert that a ValueError is raised and contains our specific recovery instruction
        with self.assertRaises(ValueError) as ctx:
            await breakdown_topic("Python")
            
        self.assertIn("RECOVERY INSTRUCTION", str(ctx.exception))
        self.assertIn("manually name 3 specific sub-topics", str(ctx.exception))

    @patch("tutor_agent.tools.get_gemini_client")
    @patch("tutor_agent.tools.verify_quiz_correctness", new_callable=AsyncMock)
    async def test_generate_quiz(self, mock_verify, mock_get_client):
        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_verify.return_value = True
        
        mock_response = MagicMock()
        mock_response.text = (
            '{"question": "What is Python?", "options": ["A", "B", "C", "D"], '
            '"correct_option": "A", "explanation": "It is a programming language."}'
        )
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        # Act
        res = await generate_quiz("Python Introduction", "beginner")
        
        # Assert
        self.assertEqual(res["question"], "What is Python?")
        self.assertEqual(res["options"], ["A", "B", "C", "D"])
        self.assertEqual(res["correct_option"], "A")
        self.assertEqual(res["explanation"], "It is a programming language.")

    @patch("tutor_agent.tools.get_gemini_client")
    async def test_generate_quiz_failure_recovery_instructions(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("Generation error"))
        
        with self.assertRaises(ValueError) as ctx:
            await generate_quiz("Loops", "beginner")
            
        self.assertIn("RECOVERY INSTRUCTION", str(ctx.exception))
        self.assertIn("dynamically constructing a single, direct, open-ended", str(ctx.exception))

    @patch("tutor_agent.tools.StudentProfileManager")
    async def test_assess_understanding(self, mock_manager_cls):
        # Setup mock
        mock_manager = AsyncMock()
        mock_manager_cls.return_value = mock_manager
        mock_manager.update_subject_score.return_value = {"score": 20, "status": "in_progress"}
        
        # Act
        res = await assess_understanding("Python Basics", True)
        
        # Assert
        self.assertEqual(res["score"], 20)
        mock_manager.load_profile.assert_called_once()
        mock_manager.update_subject_score.assert_called_once_with("Python Basics", True)

    @patch("tutor_agent.tools.StudentProfileManager")
    async def test_get_progress_summary(self, mock_manager_cls):
        mock_manager = AsyncMock()
        mock_manager_cls.return_value = mock_manager
        mock_manager.get_profile_summary.return_value = "Topic: Python"
        
        res = await get_progress_summary()
        
        self.assertEqual(res, "Topic: Python")
        mock_manager.load_profile.assert_called_once()
