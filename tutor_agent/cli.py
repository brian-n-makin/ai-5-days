import asyncio
import os
import sys
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.theme import Theme

import google.adk as adk
from google.adk.runners import InMemoryRunner

from tutor_agent.observability import setup_telemetry
from tutor_agent.orchestrator import create_tutor_app
from tutor_agent.memory import StudentProfileManager

# Custom terminal color theme for rich console
tutor_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "tutor": "bold sky_blue3",
    "student": "bold sand",
    "progress": "bold gold3",
})

console = Console(theme=tutor_theme)

async def repl_loop(runner: InMemoryRunner) -> None:
    """Runs the main interactive teaching loop."""
    console.print("\n[success]✨ Session Started! Type 'exit', 'quit', or press Ctrl+C to stop. ✨[/success]")
    
    # Send an initial greeting / resume trigger to the agent
    with console.status("[info]Initializing tutor...", spinner="dots"):
        events = await runner.run_debug("Hello! Let's get started.", quiet=True)
    
    for e in events:
        if e.content:
            for part in e.content.parts:
                if part.text:
                    console.print(Panel(part.text, title="[tutor]Tutor[/tutor]", border_style="sky_blue3"))

    while True:
        try:
            # rich Prompt is synchronous, which is normal for CLI REPL loops.
            # To keep things clean, we prompt synchronously, then run the async agent.
            user_input = Prompt.ask("\n[student]You[/student]")
            if user_input.strip().lower() in ["exit", "quit"]:
                console.print("[info]Exiting. Good luck on your learning journey! 📖[/info]")
                break
                
            if not user_input.strip():
                continue

            with console.status("[info]Tutor is thinking...", spinner="dots"):
                events = await runner.run_debug(user_input, quiet=True)
                
            for e in events:
                if e.content:
                    for part in e.content.parts:
                        if part.text:
                            console.print(Panel(part.text, title="[tutor]Tutor[/tutor]", border_style="sky_blue3"))
                            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Exiting. Good luck on your learning journey! 📖[/info]")
            break

async def async_main() -> None:
    """Async Main program logic."""
    # 1. Initialize Tracing & Observability
    setup_telemetry()
    
    console.print(Panel.fit(
        "Welcome to your AI Personal Tutor built with ADK!\n"
        "I will help you master any topic with interactive lessons and quizzes.",
        title="[tutor]AI Tutor CLI[/tutor]",
        border_style="gold3"
    ))
    
    # 2. Check for existing curriculum profiles asynchronously (Non-blocking DB operations)
    manager = StudentProfileManager()
    profile = await manager.load_profile()
    
    if profile:
        console.print("[progress]Found existing learning profile:[/progress]")
        summary = await manager.get_profile_summary()
        console.print(summary)
        resume = Confirm.ask("Would you like to resume this learning session?", default=True)
        if not resume:
            # Delete old database to start fresh
            if os.path.exists("student_profile.db"):
                os.remove("student_profile.db")
            console.print("[info]Cleared previous profile database. Starting fresh![/info]")
    
    # 3. Create the ADK App & Runner with History Compaction Enabled
    app = create_tutor_app()
    runner = InMemoryRunner(app=app)
    
    # 4. Run the REPL loop
    await repl_loop(runner)

def main() -> None:
    """Main CLI Entrypoint."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
