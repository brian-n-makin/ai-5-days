import os
import json
import shutil
import tempfile
import unittest
from tutor_agent.memory import StudentProfileManager

class TestMemory(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_student_profile.db")
        self.manager = StudentProfileManager(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_initialize_and_load_profile(self):
        topic = "Software Engineering"
        subjects = ["Testing", "Deployment", "CI/CD"]
        
        self.assertIsNone(await self.manager.load_profile())
        
        await self.manager.initialize_profile(topic, subjects)
        
        # Reload and check
        loaded = await self.manager.load_profile()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["topic"], topic)
        self.assertIn("Testing", loaded["subjects"])
        self.assertEqual(loaded["subjects"]["Testing"]["status"], "pending")
        self.assertEqual(loaded["subjects"]["Testing"]["score"], 0)

    async def test_update_subject_score(self):
        topic = "Software Engineering"
        subjects = ["Testing"]
        await self.manager.initialize_profile(topic, subjects)
        
        # Correct answer -> score + 20
        res = await self.manager.update_subject_score("Testing", correct=True)
        self.assertEqual(res["score"], 20)
        self.assertEqual(res["status"], "in_progress")
        self.assertEqual(res["quizzes_taken"], 1)
        self.assertEqual(res["quizzes_passed"], 1)
        
        # Incorrect answer -> score - 10, but min 0
        res = await self.manager.update_subject_score("Testing", correct=False)
        self.assertEqual(res["score"], 10)
        self.assertEqual(res["quizzes_taken"], 2)
        self.assertEqual(res["quizzes_passed"], 1)
        
        # Transition to mastered
        for _ in range(4):
            res = await self.manager.update_subject_score("Testing", correct=True)
        
        self.assertEqual(res["score"], 90)
        self.assertEqual(res["status"], "mastered")
