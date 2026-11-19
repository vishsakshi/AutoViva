from typing import Any, Dict, Iterable, List


def group_evaluation_records(records: Iterable[Any]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple, List[Any]] = {}
    for record in records:
        if record.attempt_id:
            key = (record.student_id, record.viva_id, record.attempt_id)
        else:
            key = (record.student_id, record.viva_id, f"legacy:{record.evaluation_id}")
        grouped.setdefault(key, []).append(record)

    sessions = []
    for (student_id, viva_id, attempt_key), session_records in grouped.items():
        session_records.sort(key=lambda record: (
            record.question_number is None,
            record.question_number if record.question_number is not None else 0,
            record.created_at,
        ))
        summaries = [
            record.faculty_version_v2.evaluation_summary
            if record.current_version > 1 and record.faculty_version_v2
            else record.ai_version_v1.evaluation_summary
            for record in session_records
        ]
        statuses = {record.status.value for record in session_records}
        sessions.append({
            "session_id": attempt_key,
            "attempt_id": session_records[0].attempt_id,
            "legacy": session_records[0].attempt_id is None,
            "student_id": student_id,
            "viva_id": viva_id,
            "started_at": session_records[0].attempt_started_at or min(
                record.created_at for record in session_records
            ),
            "question_count": len(session_records),
            "total_marks": round(sum(summary.final_score for summary in summaries), 2),
            "max_marks": round(sum(summary.max_score for summary in summaries), 2),
            "status": statuses.pop() if len(statuses) == 1 else "MIXED",
            "evaluations": session_records,
        })

    sessions.sort(key=lambda session: session["started_at"] or "", reverse=True)
    return sessions
