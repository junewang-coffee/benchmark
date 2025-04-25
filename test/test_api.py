import json
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from app.models import Evaluation, StandardAnswer


@pytest.mark.django_db
def test_single_evaluate(client) -> None:
    """
    Test the single evaluation API.

    Parameters
    ----------
    client : Any
        The Django test client.
    """
    StandardAnswer.objects.create(source="source1", content="Artificial Intelligence")

    payload = {
        "exp_id": "proj001",
        "question_id": "q123",
        "test_question": "What is AI?",
        "question_source": "source1",
        "bot_response": "Artificial Intelligence is the simulation of human thinking.",
    }

    response = client.post("/api/evaluate", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["question_id"] == "q123"
    assert Evaluation.objects.filter(exp_id="proj001", question_id="q123").exists()


@pytest.mark.django_db
def test_batch_evaluate(client) -> None:
    """
    Test the batch evaluation API.

    Parameters
    ----------
    client : Any
        The Django test client.
    """
    StandardAnswer.objects.create(source="source1", content="AI stands for Artificial Intelligence")

    batch_data = [
        {
            "exp_id": "proj_batch",
            "test_question": "Explain AI",
            "question_source": "source1",
            "bot_response": "AI stands for Artificial Intelligence",
        },
        {
            "exp_id": "proj_batch",
            "test_question": "What is AI used for?",
            "question_source": "source1",
            "bot_response": "Artificial Intelligence is used in many fields",
        },
    ]

    response = client.post("/api/evaluate/batch", data=json.dumps(batch_data), content_type="application/json")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert Evaluation.objects.filter(exp_id="proj_batch").count() == 2


@pytest.mark.django_db
def test_get_evaluation_by_question_id(client) -> None:
    """
    Test retrieving an evaluation by question ID.

    Parameters
    ----------
    client : Any
        The Django test client.
    """
    Evaluation.objects.create(
        exp_id="proj999",
        question_id="q999",
        test_question="Sample?",
        bot_response="Sample.",
        question_source="source_x",
        standard_answer="Sample",
        difficulty=1,
        accuracy=3,
        relevance=3,
        logic=3,
        conciseness=3,
        language_quality=3,
        total_score=15,
    )
    response = client.get("/api/evaluation/q999")
    assert response.status_code == 200
    assert response.json()["total_score"] == 15


@pytest.mark.django_db
def test_get_project_evaluations(client) -> None:
    """
    Test retrieving evaluations for a specific project.

    Parameters
    ----------
    client : Any
        The Django test client.
    """
    Evaluation.objects.create(
        exp_id="proj_get",
        question_id="q001",
        test_question="Test?",
        bot_response="Answer.",
        question_source="src",
        standard_answer="Answer",
        difficulty=1,
        accuracy=3,
        relevance=3,
        logic=3,
        conciseness=3,
        language_quality=3,
        total_score=15,
    )
    response = client.get("/api/project/proj_get/evaluations")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_upload_json(client) -> None:
    """
    Test uploading a JSON file for evaluation.

    Parameters
    ----------
    client : Any
        The Django test client.
    """
    json_data = [
        {
            "question_id": "up001",
            "question": "What is AI?",
            "response": "AI is the simulation of human intelligence.",
            "sources": [{"title": "Wikipedia", "content": "AI is the simulation of human intelligence."}],
        }
    ]
    StandardAnswer.objects.create(source="Wikipedia", content="AI is the simulation of human intelligence.")
    json_file = SimpleUploadedFile("data.json", json.dumps(json_data).encode(), content_type="application/json")

    response = client.post(
        "/api/upload_json?project_id=upload001",
        data={"file": json_file},
        format="multipart",
    )
    assert response.status_code == 200
    assert Evaluation.objects.filter(exp_id="upload001", question_id="up001").exists()