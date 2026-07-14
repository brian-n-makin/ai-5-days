import unittest
import google.adk as adk
from google.adk.apps.app import App
from google.adk.apps._configs import EventsCompactionConfig
from tutor_agent.orchestrator import create_tutor_agent, create_tutor_app

class TestOrchestrator(unittest.TestCase):

    def test_create_tutor_agent(self):
        root_agent = create_tutor_agent()
        self.assertIsInstance(root_agent, adk.Agent)
        self.assertEqual(root_agent.name, "TutorSystem")
        self.assertEqual(root_agent.model, "gemini-3-flash")
        
        # Verify hierarchical multi-agent structure is established
        self.assertEqual(len(root_agent.sub_agents), 3)
        sub_agent_names = [sa.name for sa in root_agent.sub_agents]
        self.assertIn("CurriculumPlannerAgent", sub_agent_names)
        self.assertIn("TutorAgent", sub_agent_names)
        self.assertIn("EvaluationQuizAgent", sub_agent_names)

        # Verify the specialized tools are distributed on the correct sub-agent
        planner = next(sa for sa in root_agent.sub_agents if sa.name == "CurriculumPlannerAgent")
        self.assertEqual(planner.model, "gemini-3-flash")
        planner_tools = [getattr(t, "__name__", "") for t in planner.tools]
        self.assertIn("breakdown_topic", planner_tools)
        self.assertIn("get_progress_summary", planner_tools)

        tutor = next(sa for sa in root_agent.sub_agents if sa.name == "TutorAgent")
        self.assertEqual(tutor.model, "gemini-3.5-flash")
        self.assertEqual(len(tutor.tools), 0)  # No tools needed, pure conversational lecturing

        quiz_master = next(sa for sa in root_agent.sub_agents if sa.name == "EvaluationQuizAgent")
        self.assertEqual(quiz_master.model, "gemini-3.5-flash")
        quiz_tools = [getattr(t, "__name__", "") for t in quiz_master.tools]
        self.assertIn("generate_quiz", quiz_tools)
        self.assertIn("assess_understanding", quiz_tools)

    def test_create_tutor_app(self):
        app = create_tutor_app()
        self.assertIsInstance(app, App)
        self.assertEqual(app.name, "TutorApp")
        self.assertIsNotNone(app.events_compaction_config)
        self.assertIsInstance(app.events_compaction_config, EventsCompactionConfig)
        self.assertEqual(app.events_compaction_config.compaction_interval, 4)
        self.assertEqual(app.events_compaction_config.overlap_size, 1)
