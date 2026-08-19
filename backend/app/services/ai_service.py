import logging
from typing import Dict, Any, List
from app.services.llm_service import llm_service

logger = logging.getLogger("vivabot.services.ai")

class AIService:
    """
    Unified AI Service adapter delegating directly to LLMService.
    """
    def __init__(self):
        self.llm = llm_service

    async def generate_questions(self, subject: str, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"AI Service: Delegating question generation for '{subject}' - '{topic}' to LLMService")
        res = self.llm.generate_viva_question(
            evidence_chunks=[{"text": f"Subject: {subject}. Core Topic: {topic}."}],
            topic_title=topic,
            section_title=subject,
            difficulty="Medium",
            bloom_level="Understand"
        )
        return [res]

    async def evaluate_answer(self, question: str, student_answer: str, expected_key_points: List[str]) -> Dict[str, Any]:
        logger.info("AI Service: Delegating answer evaluation to LLMService")
        rubric = [{"criterion": kp, "marks": round(10.0 / max(1, len(expected_key_points)), 1)} for kp in expected_key_points]
        return self.llm.evaluate_student_answer(
            question_text=question,
            ideal_answer=" ".join(expected_key_points),
            rubric=rubric,
            student_answer=student_answer
        )

ai_service = AIService()
