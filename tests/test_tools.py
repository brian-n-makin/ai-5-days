import unittest
from unittest.mock import patch, MagicMock
from tutor_agent.tools import (
    breakdown_topic,
    generate_quiz,
    assess_understanding,
    get_progress_summary,
    Curriculum,
    Quiz
)
from tutor_agent.memory import StudentProfileManager

class TestTools(unittest.TestCase):

    @patch("tutor_agent.tools.get_gemini_client")
    @patch("tutor_agent.tools.StudentProfileManager")
    def test_breakdown_topic(self, mock_manager_cls, mock_get_client):
        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        # Mocking structured output text
        mock_response.text = '{"subjects": ["Variables", "Loops", "Functions"]}'
        mock_client.models.generate_content.return_value = mock_response
        
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager
        
        # Act
        res = breakdown_topic("Python")
        
        # Assert
        self.assertEqual(res, ["Variables", "Loops", "Functions"])
        mock_manager.initialize_profile.assert_called_once_with("Python", ["Variables", "Loops", "Functions"])

    @patch("tutor_agent.tools.get_gemini_client")
    def test_generate_quiz(self, mock_get_client):
        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = (
            '{"question": "What is Python?", "options": ["A", "B", "C", "D"], '
            '"correct_option": "A", "explanation": "It is a programming language."}'
        )
        mock_client.models.generate_content.return_value = mock_response
        
        # Act
        res = generate_quiz("Python Introduction", "beginner")
        
        # Assert
        self.assertEqual(res["question"], "What is Python?")
        self.assertEqual(res["options"], ["A", "B", "C", "D"])
        self.assertEqual(res["correct_option"], "A")
        self.assertEqual(res["explanation"], "It is a programming language.")

    @patch("tutor_agent.tools.StudentProfileManager")
    def test_assess_understanding(self, mock_manager_cls):
        # Setup mock
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager
        mock_manager.update_subject_score.return_value = {"score": 20, "status": "in_progress"}
        
        # Act
        res = assess_understanding("Python Basics", True)
        
        # Assert
        self.assertEqual(res["score"], 20)
        mock_manager.load_profile.assert_called_once()
        mock_manager.update_subject_score.assert_called_once_with("Python Basics", True)

    @patch("tutor_agent.tools.StudentProfileManager")
    def test_get_progress_summary(self, mock_manager_cls):
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager
        mock_manager.get_profile_summary.return_value = "Topic: Python"
        
        res = get_progress_summary()
        
        self.assertEqual(res, "Topic: Python")
        mock_manager.load_profile.assert_called_once()
