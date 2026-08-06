import logging
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("vivabot.services.ai")

class AIService:
    """
    Decoupled AI Service for LLM-backed viva question generation,
    real-time response evaluation, and analytics feedback.
    """
    def __init__(self):
        self.api_url = settings.LLM_API_URL
        self.api_key = settings.LLM_API_KEY

    async def generate_questions(self, subject: str, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"AI Service Stub: Generating {count} questions for subject '{subject}', topic '{topic}'")
        # Placeholder logic for Phase 0 skeleton
        return [
            {
                "topic": topic,
                "question_text": f"Sample question #{i+1} on {topic} for {subject}",
                "difficulty": "medium",
                "expected_key_points": ["key point 1", "key point 2"]
            }
            for i in range(count)
        ]

    async def evaluate_answer(self, question: str, student_answer: str, expected_key_points: List[str]) -> Dict[str, Any]:
        logger.info("AI Service Stub: Evaluating student answer")
        # Placeholder evaluation for Phase 0 skeleton
        return {
            "score": 8.5,
            "feedback": "Good answer covering primary concepts.",
            "key_points_covered": expected_key_points
        }

ai_service = AIService()
