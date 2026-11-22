import pytest

import app.services.viva_creation_service as viva_creation_module
from app.services.viva_creation_service import VivaCreationService, VivaSessionRecord


def make_service_and_record(monkeypatch, generated_questions, question_count=2):
    record = VivaSessionRecord(
        viva_id="viva-test",
        subject="Computer Science",
        course_code="CS101",
        topic="Networks",
        question_count=question_count,
        duration_minutes=15,
        batch="Batch 2026",
        created_at="2026-11-22 12:00:00",
    )
    service = VivaCreationService.__new__(VivaCreationService)
    def get_viva(viva_id):
        assert viva_id == record.viva_id
        return record

    def sync_to_mongo(saved_record):
        assert saved_record is record

    def generate_questions(**kwargs):
        assert kwargs["requested_count"] == question_count
        return {
            "status": "SUCCESS",
            "generated_questions": generated_questions,
        }

    monkeypatch.setattr(service, "get_viva", get_viva)
    monkeypatch.setattr(service, "_sync_to_mongo", sync_to_mongo)
    monkeypatch.setattr(
        viva_creation_module.question_generator_engine,
        "generate_document_grounded_questions",
        generate_questions,
    )
    return service, record


def test_generation_trims_surplus_questions_to_requested_count(monkeypatch):
    questions = [
        {"question_id": "q1"},
        {"question_id": "q2"},
        {"question_id": "q3"},
    ]
    service, record = make_service_and_record(monkeypatch, questions)

    updated_record = service.generate_questions_for_viva(record.viva_id)

    assert [question["question_id"] for question in updated_record.generated_questions] == ["q1", "q2"]
    assert len(updated_record.generated_questions) == record.question_count


def test_generation_rejects_too_few_questions(monkeypatch):
    service, record = make_service_and_record(monkeypatch, [{"question_id": "q1"}])

    with pytest.raises(ValueError, match="Unable to generate exactly 2 questions"):
        service.generate_questions_for_viva(record.viva_id)

    assert record.generated_questions == []
