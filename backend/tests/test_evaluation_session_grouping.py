from types import SimpleNamespace

from app.models.review_module import EvaluationStatus
from app.services.evaluation_session_grouping import group_evaluation_records


def make_record(
    evaluation_id,
    student_id,
    viva_id,
    attempt_id,
    question_number,
    score,
    max_score,
    created_at,
):
    summary = SimpleNamespace(final_score=score, max_score=max_score)
    return SimpleNamespace(
        evaluation_id=evaluation_id,
        student_id=student_id,
        viva_id=viva_id,
        attempt_id=attempt_id,
        attempt_started_at="2026-10-06T10:00:00+00:00" if attempt_id else None,
        question_number=question_number,
        created_at=created_at,
        status=EvaluationStatus.PENDING_REVIEW,
        current_version=1,
        faculty_version_v2=None,
        ai_version_v1=SimpleNamespace(evaluation_summary=summary),
    )


def test_groups_keep_students_and_attempts_separate_and_order_questions():
    sessions = group_evaluation_records([
        make_record("q2-a", "student-a", "viva-1", "attempt-a", 2, 2.5, 3, "2026-10-06T10:02:00"),
        make_record("q1-a", "student-a", "viva-1", "attempt-a", 1, 3, 4, "2026-10-06T10:01:00"),
        make_record("q1-b", "student-a", "viva-1", "attempt-b", 1, 1, 2, "2026-10-06T11:01:00"),
        make_record("q1-other", "student-b", "viva-1", "attempt-a", 1, 2, 2, "2026-10-06T10:01:00"),
    ])

    assert len(sessions) == 3
    attempt_a_student = next(
        session for session in sessions
        if session["attempt_id"] == "attempt-a" and session["student_id"] == "student-a"
    )
    assert [record.evaluation_id for record in attempt_a_student["evaluations"]] == ["q1-a", "q2-a"]
    assert attempt_a_student["question_count"] == 2
    assert attempt_a_student["total_marks"] == 5.5
    assert attempt_a_student["max_marks"] == 7


def test_legacy_evaluations_without_attempt_id_are_never_merged():
    sessions = group_evaluation_records([
        make_record("legacy-1", "student-a", "viva-1", None, 1, 2, 3, "2026-10-06T10:01:00"),
        make_record("legacy-2", "student-a", "viva-1", None, 2, 1, 3, "2026-10-06T10:02:00"),
    ])

    assert len(sessions) == 2
    assert {session["session_id"] for session in sessions} == {"legacy:legacy-1", "legacy:legacy-2"}
    assert all(session["legacy"] and session["question_count"] == 1 for session in sessions)
