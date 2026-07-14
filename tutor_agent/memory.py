import json
import os
import aiosqlite
from typing import Dict, Any, Optional, List

class StudentProfileManager:
    """Manages persistent student profiles tracking curriculum progress and mastery scores using a SQLite database."""

    def __init__(self, db_path: str = "student_profile.db"):
        self.db_path = db_path
        self.profile: Dict[str, Any] = {}

    async def init_db(self) -> None:
        """Asynchronously initializes the database and creates the profile table if it does not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY,
                    topic TEXT NOT NULL,
                    subjects TEXT NOT NULL
                )
            ''')
            await db.commit()

    async def load_profile(self) -> Optional[Dict[str, Any]]:
        """Asynchronously loads the student profile from the database."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT topic, subjects FROM profile ORDER BY id DESC LIMIT 1') as cursor:
                row = await cursor.fetchone()
                if row:
                    self.profile = {
                        "topic": row[0],
                        "subjects": json.loads(row[1])
                    }
                    return self.profile
        self.profile = {}
        return None

    async def initialize_profile(self, topic: str, subjects: List[str]) -> Dict[str, Any]:
        """Asynchronously initializes a brand new curriculum profile for a given topic."""
        await self.init_db()
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
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clear previous profile data to start fresh
            await db.execute('DELETE FROM profile')
            await db.execute(
                'INSERT INTO profile (topic, subjects) VALUES (?, ?)',
                (topic, json.dumps(self.profile["subjects"]))
            )
            await db.commit()
            
        return self.profile

    async def update_subject_score(self, subject: str, correct: bool) -> Dict[str, Any]:
        """Asynchronously updates mastery scores and flags based on quiz correctness."""
        # Ensure profile is loaded
        if not self.profile:
            await self.load_profile()
            if not self.profile:
                raise ValueError("No profile initialized in database.")
        
        subjects = self.profile["subjects"]
        if subject not in subjects:
            subjects[subject] = {
                "status": "in_progress",
                "score": 0,
                "quizzes_taken": 0,
                "quizzes_passed": 0
            }

        subj_data = subjects[subject]
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

        # Persist updated profile subjects to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE profile SET subjects = ? WHERE topic = ?',
                (json.dumps(subjects), self.profile["topic"])
            )
            await db.commit()
            
        return subj_data

    async def get_subject_mastery(self, subject: str) -> Optional[Dict[str, Any]]:
        """Asynchronously retrieves mastery metadata for a specific subject."""
        if not self.profile:
            await self.load_profile()
            
        if self.profile and "subjects" in self.profile:
            return self.profile["subjects"].get(subject)
        return None

    async def get_profile_summary(self) -> str:
        """Asynchronously generates a human-friendly progress report of the student."""
        if not self.profile:
            await self.load_profile()
            
        if not self.profile:
            return "No active curriculum profile loaded."
        
        summary = f"Topic: {self.profile.get('topic', 'Unknown')}\n"
        summary += "Curriculum Breakdown:\n"
        for subj, data in self.profile.get("subjects", {}).items():
            status_emoji = "✅" if data["status"] == "mastered" else "📖" if data["status"] == "in_progress" else "⏳"
            summary += f"  - {status_emoji} {subj}: Mastery {data['score']}% (Quizzes: {data['quizzes_passed']}/{data['quizzes_taken']})\n"
        return summary
