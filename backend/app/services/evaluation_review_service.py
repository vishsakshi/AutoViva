import copy
import uuid
import logging
from typing import List, Dict, Any, Optional

from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.feedback_module import GenerateFeedbackRequest, FeedbackModule3Response, CriterionFeedbackItem
from app.models.review_module import (
    FullEvaluationRecord,
    EvaluationStatus,
    FacultyAction,
    FacultyOverrideRequest,
    FacultyAuditLogEntry
)
from app.services.evaluation_engine import evaluation_engine_module1
from app.services.scoring_engine import scoring_engine_module2
from app.services.feedback_engine import feedback_engine_module3

logger = logging.getLogger("vivabot.services.evaluation_review")

class EvaluationReviewServiceModule4:
    """
    Module 4 Faculty Review Service:
    - End-to-End Pipeline Submission (Module 1 -> Module 2 -> Module 3 -> Staged PENDING_REVIEW)
    - Immutability of AI Version 1
    - Faculty Modification creating Version 2
    - Comprehensive Audit Logging
    - Status management (PENDING_REVIEW, APPROVED, REJECTED, OVERRIDDEN)
    """
    def __init__(self):
        # Storage for evaluation records and audit history
        self.evaluations_db: Dict[str, FullEvaluationRecord] = {}
        self.global_audit_logs: List[FacultyAuditLogEntry] = []

    def submit_student_answer_pipeline(
        self,
        req: EvaluateAnswerRequest,
        question_id: str = "vq_com_ip_4198fe",
        student_id: str = "std_10293"
    ) -> FullEvaluationRecord:
        """
        Runs complete evaluation pipeline:
        Module 1 (Classification) -> Module 2 (Scoring) -> Module 3 (Feedback) -> Staged as PENDING_REVIEW
        """
        # Run Module 1
        m1_res = evaluation_engine_module1.evaluate_answer_module1(req)
        
        # Run Module 2
        m2_res = scoring_engine_module2.calculate_scores(m1_res.evaluation_id, m1_res.criterion_evaluations)

        # Run Module 3
        fb_req = GenerateFeedbackRequest(
            question_text=req.question_text,
            ideal_answer=req.ideal_answer,
            student_answer=req.student_answer,
            module1_result=m1_res,
            module2_result=m2_res
        )
        fb_res = feedback_engine_module3.generate_feedback_report(fb_req)

        # Create Full Record (AI Version 1)
        record = FullEvaluationRecord(
            evaluation_id=m1_res.evaluation_id,
            question_id=question_id,
            student_id=student_id,
            question_text=req.question_text,
            ideal_answer=req.ideal_answer,
            student_answer=req.student_answer,
            status=EvaluationStatus.PENDING_REVIEW,
            current_version=1,
            ai_version_v1=fb_res,
            faculty_version_v2=None,
            audit_history=[]
        )

        self.evaluations_db[record.evaluation_id] = record
        logger.info(f"Pipeline Submission complete [{record.evaluation_id}]: Staged PENDING_REVIEW. AI Score={fb_res.evaluation_summary.final_score}/10.")
        return record

    def get_pending_evaluations(self) -> List[FullEvaluationRecord]:
        return [r for r in self.evaluations_db.values() if r.status == EvaluationStatus.PENDING_REVIEW]

    def get_all_evaluations(self) -> List[FullEvaluationRecord]:
        return list(self.evaluations_db.values())


    def get_evaluation_by_id(self, eval_id: str) -> Optional[FullEvaluationRecord]:
        return self.evaluations_db.get(eval_id)

    def get_evaluation_history(self, eval_id: str) -> List[FacultyAuditLogEntry]:
        record = self.evaluations_db.get(eval_id)
        return record.audit_history if record else []


    def _log_faculty_action(
        self,
        record: FullEvaluationRecord,
        action: FacultyAction,
        prev_score: float,
        new_score: float,
        reason: str,
        comment: str
    ) -> FacultyAuditLogEntry:
        log_entry = FacultyAuditLogEntry(
            log_id=f"audit_{uuid.uuid4().hex[:8]}",
            evaluation_id=record.evaluation_id,
            faculty_action=action,
            previous_score=prev_score,
            new_score=new_score,
            reason_for_change=reason,
            faculty_comment=comment
        )
        record.audit_history.append(log_entry)
        self.global_audit_logs.append(log_entry)
        logger.info(f"Audit Log Recorded [{log_entry.log_id}]: Action={action}, PrevScore={prev_score}, NewScore={new_score}")
        return log_entry

    def approve_evaluation(self, eval_id: str, faculty_comment: str = "") -> FullEvaluationRecord:
        record = self.evaluations_db.get(eval_id)
        if not record:
            raise ValueError(f"Evaluation '{eval_id}' not found.")

        current_score = record.ai_version_v1.evaluation_summary.final_score if record.current_version == 1 else record.faculty_version_v2.evaluation_summary.final_score
        
        record.status = EvaluationStatus.APPROVED
        self._log_faculty_action(
            record=record,
            action=FacultyAction.APPROVE,
            prev_score=current_score,
            new_score=current_score,
            reason="Faculty approved AI evaluation without score edits.",
            comment=faculty_comment
        )
        logger.info(f"Evaluation [{eval_id}] APPROVED by faculty.")
        return record

    def reject_evaluation(self, eval_id: str, reason_for_change: str = "Unsatisfactory evaluation", faculty_comment: str = "") -> FullEvaluationRecord:
        record = self.evaluations_db.get(eval_id)
        if not record:
            raise ValueError(f"Evaluation '{eval_id}' not found.")

        current_score = record.ai_version_v1.evaluation_summary.final_score if record.current_version == 1 else record.faculty_version_v2.evaluation_summary.final_score

        record.status = EvaluationStatus.REJECTED
        self._log_faculty_action(
            record=record,
            action=FacultyAction.REJECT,
            prev_score=current_score,
            new_score=0.0,
            reason=reason_for_change,
            comment=faculty_comment
        )
        logger.info(f"Evaluation [{eval_id}] REJECTED by faculty.")
        return record

    def override_evaluation(self, eval_id: str, req: FacultyOverrideRequest) -> FullEvaluationRecord:
        record = self.evaluations_db.get(eval_id)
        if not record:
            raise ValueError(f"Evaluation '{eval_id}' not found.")

        # Immuntability Check: Copy Version 1 to create Version 2
        v1 = record.ai_version_v1
        v2 = copy.deepcopy(v1)

        prev_score = v1.evaluation_summary.final_score

        # Apply Criterion Score Overrides if provided
        if req.criterion_score_overrides:
            new_total = 0.0
            for item in v2.criterion_feedback:
                if item.criterion_id in req.criterion_score_overrides:
                    override_marks = float(req.criterion_score_overrides[item.criterion_id])
                    item.earned_marks = override_marks
                    item.feedback_note = f"Faculty modified criterion score to {override_marks}/{item.allocated_marks} marks."
                new_total += item.earned_marks
            
            v2.evaluation_summary.final_score = round(new_total, 2)
            v2.evaluation_summary.percentage = round((new_total / v2.evaluation_summary.max_score) * 100.0, 2)

        # Apply Overall Score Override if explicitly set
        if req.new_score is not None:
            v2.evaluation_summary.final_score = float(req.new_score)
            v2.evaluation_summary.percentage = round((req.new_score / v2.evaluation_summary.max_score) * 100.0, 2)

        new_score = v2.evaluation_summary.final_score

        # Update Record to Version 2 & Status
        record.faculty_version_v2 = v2
        record.current_version = 2
        record.status = EvaluationStatus.OVERRIDDEN

        # Record Audit Log
        self._log_faculty_action(
            record=record,
            action=FacultyAction.OVERRIDE,
            prev_score=prev_score,
            new_score=new_score,
            reason=req.reason_for_change or "Faculty modified evaluation score.",
            comment=req.faculty_comment or ""
        )

        logger.info(f"Evaluation [{eval_id}] OVERRIDDEN: Version 1 ({prev_score}) -> Version 2 ({new_score}). Version 1 preserved.")
        return record

evaluation_review_service = EvaluationReviewServiceModule4()
