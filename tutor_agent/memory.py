import json
import os
from typing import Dict, Any, Optional, List

class StudentProfileManager:
    """Manages persistent student profiles tracking curriculum progress and mastery scores."""

    def __init__(self, file_path: str = "student_profile.json"):
        self.file_path = file_path
        self.profile: Dict[str, Any] = {}

    def load_profile(self) -> Optional[Dict[str, Any]]:
        """Loads the student profile from the persistent store if it exists."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.profile = json.load(f)
                    return self.profile
            except (json.JSONDecodeError, IOError) as e:
                # Fallback or re-raise based on severity; for safety, return empty and log
                self.profile = {}
                return None
        return None

    def initialize_profile(self, topic: str, subjects: List[str]) -> Dict[str, Any]:
        """Initializes a brand new curriculum profile for a given topic."""
        self.profile = {
            "topic": topic,
            "subjects": {
                subj: {
                    "status": "pending",  # pending, in_progress, mastered
                    "score": 0,            # 0 to 100 mastery rating
                    "quizzes_taken": 0,
                    "quizzes_passed": 0,
                }
                for subj in subjects
            }
        }
        self.save_profile()
        return self.profile

    def update_subject_score(self, subject: str, correct: bool) -> Dict[str, Any]:
        """Updates mastery scores and flags based on quiz correctness."""
        if not self.profile or "subjects" not in self.profile:
            raise ValueError("No profile initialized.")
        
        if subject not in self.profile["subjects"]:
            # If the subject wasn't explicitly generated in the original breakdown, add it dynamically
            self.profile["subjects"][subject] = {
                "status": "in_progress",
                "score": 0,
                "quizzes_taken": 0,
                "quizzes_passed": 0
            }

        subj_data = self.profile["subjects"][subject]
        subj_data["quizzes_taken"] += 1
        
        old_score = subj_data.get("score", 0)
        if correct:
            subj_data["quizzes_passed"] += 1
            # Standard mastery growth: +20 points for correct answer
            new_score = min(old_score + 20, 100)
        else:
            # Standard recovery rate: -10 points on incorrect answer
            new_score = max(old_score - 10, 0)
            
        subj_data["score"] = new_score
        
        # Determine status transitions
        if new_score >= 80:
            subj_data["status"] = "mastered"
        elif new_score > 0:
            subj_data["status"] = "in_progress"
        else:
            subj_data["status"] = "pending"

        self.save_profile()
        return subj_data

    def get_subject_mastery(self, subject: str) -> Optional[Dict[str, Any]]:
        """Retrieves mastery metadata for a specific subject."""
        if self.profile and "subjects" in self.profile:
            return self.profile["subjects"].get(subject)
        return None

    def get_profile_summary(self) -> str:
        """Generates a human-friendly progress report of the student."""
        if not self.profile:
            return "No active curriculum profile loaded."
        
        summary = f"Topic: {self.profile.get('topic', 'Unknown')}\n"
        summary += "Curriculum Breakdown:\n"
        for subj, data in self.profile.get("subjects", {}).items():
            status_emoji = "✅" if data["status"] == "mastered" else "📖" if data["status"] == "in_progress" else "⏳"
            summary += f"  - {status_emoji} {subj}: Mastery {data['score']}% (Quizzes: {data['quizzes_passed']}/{data['quizzes_taken']})\n"
        return summary

    def save_profile(self) -> None:
        """Persists the profile to disk."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=2)
