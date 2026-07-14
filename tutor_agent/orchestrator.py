import os
import google.adk as adk
from google.adk.apps.app import App
from google.adk.apps._configs import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models.google_llm import Gemini

from tutor_agent.tools import (
    breakdown_topic,
    generate_quiz,
    assess_understanding,
    get_progress_summary
)

# -------------------------------------------------------------
# 1. Multi-Agent System: Prompts and Instructions
# -------------------------------------------------------------

PLANNER_INSTRUCTION = """You are the CurriculumPlannerAgent. Your job is to break down the student's requested topic and monitor progress.

Responsibilities:
1. If no profile/curriculum exists yet, ask the student what topic they want to learn. Once they provide a topic, IMMEDIATELY call `breakdown_topic` to generate a curriculum outline.
2. If they have an active curriculum, greet them and call `get_progress_summary` to see what subjects are pending.
3. Introduce the active sub-topic to the student, and then IMMEDIATELY call `transfer_to_agent(agent_name='TutorAgent')` to let the TutorAgent explain the concept.
"""

TUTOR_INSTRUCTION = """You are the TutorAgent. Your job is to teach the concepts of the active subject thoroughly, answer clarifying questions, and ensure complete understanding.

Responsibilities:
1. Explain the concepts clearly, idiomatically, step-by-step, using concrete examples or code blocks where applicable.
2. Encourage the user to ask questions, and address their doubts with high educational value.
3. Once they seem to understand, or if they ask to be tested/quizzed, call `transfer_to_agent(agent_name='EvaluationQuizAgent')` to evaluate their knowledge.
"""

QUIZ_INSTRUCTION = """You are the EvaluationQuizAgent. Your job is to test the user's understanding using dynamic quizzes and update their progress.

Responsibilities:
1. Call `generate_quiz` with the current subject name and difficulty level (beginner if score is <40, intermediate if 40-70, advanced if >70).
2. Display the generated question and its 4 multiple choice options clearly to the user. Wait for their response.
3. Once they respond with their answer, determine if they are correct.
4. IMMEDIATELY call `assess_understanding` with the subject and whether they were correct to update their progress database.
5. Provide helpful feedback and explanation.
6. Call `transfer_to_agent(agent_name='TutorAgent')` to return to learning and concept guidance.
"""

SYSTEM_ROUTER_INSTRUCTION = """You are the TutorSystem root coordinator.

Your ONLY job is to greet the student upon startup and immediately call `transfer_to_agent(agent_name='CurriculumPlannerAgent')` to delegate the curriculum planning and progress tracking. Do not teach, quiz, or manage the curriculum yourself.
"""

# -------------------------------------------------------------
# 2. Agent Factory Functions
# -------------------------------------------------------------

def create_tutor_agent() -> adk.Agent:
    """Creates the collaborative multi-agent hierarchical network."""
    # A. Strategic Model Routing: Assign specific models matching role complexity
    planner = adk.Agent(
        name="CurriculumPlannerAgent",
        description="Handles curriculum breakdown and syllabus tracking.",
        instruction=PLANNER_INSTRUCTION,
        model="gemini-3-flash",  # Fast model optimized for structural breakdowns
        tools=[breakdown_topic, get_progress_summary]
    )

    tutor = adk.Agent(
        name="TutorAgent",
        description="Dedicated conversational instructor that explains subjects.",
        instruction=TUTOR_INSTRUCTION,
        model="gemini-3.5-flash",  # High reasoning, highly conversational model
        tools=[]
    )

    quiz_master = adk.Agent(
        name="EvaluationQuizAgent",
        description="Generates quizzes, assesses student answers, and updates grades.",
        instruction=QUIZ_INSTRUCTION,
        model="gemini-3.5-flash",  # High reasoning model for quiz generation
        tools=[generate_quiz, assess_understanding]
    )

    # B. Root Router Agent orchestrating the sub-agents
    root_coordinator = adk.Agent(
        name="TutorSystem",
        description="Root router coordinating the specialized multi-agent teaching assistants.",
        instruction=SYSTEM_ROUTER_INSTRUCTION,
        model="gemini-3-flash",
        sub_agents=[planner, tutor, quiz_master]  # Binds sub-agents for automated transfer_to_agent
    )
    
    return root_coordinator


def create_tutor_app() -> App:
    """Creates and returns the ADK App with history compaction configured."""
    agent = create_tutor_agent()
    
    # Configure the underlying LLM for compaction
    base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
    llm = Gemini(model="gemini-3.5-flash", base_url=base_url)
    
    # Configure sliding window event compaction (History Compaction)
    compaction_config = EventsCompactionConfig(
        summarizer=LlmEventSummarizer(llm=llm),
        compaction_interval=4,  # Compact every 4 dialog turns to save context tokens
        overlap_size=1          # Overlap by 1 turn to retain immediate context
    )
    
    app = App(
        name="TutorApp",
        root_agent=agent,
        events_compaction_config=compaction_config
    )
    return app
