import unittest
import google.adk as adk
from google.adk.apps.app import App
from google.adk.apps._configs import EventsCompactionConfig
from tutor_agent.orchestrator import create_tutor_agent, create_tutor_app

class TestOrchestrator(unittest.TestCase):

    def test_create_tutor_agent(self):
        agent = create_tutor_agent()
        self.assertIsInstance(agent, adk.Agent)
        self.assertEqual(agent.name, "TutorAgent")
        self.assertEqual(agent.model, "gemini-3.5-flash")
        
        # Verify tools are registered
        tool_names = [getattr(t, "__name__", "") for t in agent.tools]
        self.assertIn("breakdown_topic", tool_names)
        self.assertIn("generate_quiz", tool_names)
        self.assertIn("assess_understanding", tool_names)
        self.assertIn("get_progress_summary", tool_names)

    def test_create_tutor_app(self):
        app = create_tutor_app()
        self.assertIsInstance(app, App)
        self.assertEqual(app.name, "TutorApp")
        self.assertIsNotNone(app.events_compaction_config)
        self.assertIsInstance(app.events_compaction_config, EventsCompactionConfig)
        self.assertEqual(app.events_compaction_config.compaction_interval, 4)
        self.assertEqual(app.events_compaction_config.overlap_size, 1)
