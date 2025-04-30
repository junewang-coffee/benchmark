import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from app.models import Evaluation, ExamPaperQuestion, UploadedEvaluationBatch, UploadedTestPaper


@pytest.mark.django_db
def test_uploaded_evaluation_batch_creates_evaluations(client):
    """Test that uploading an evaluation batch creates corresponding evaluations in the database."""
    json_data = json.dumps([
        {
            "question_id": "q1",
            "question": "What is AI?",
            "response": "AI is artificial intelligence.",
            "sources": [{"content": "Artificial intelligence is the simulation of human intelligence."}]
        }
    ])

    json_file = SimpleUploadedFile("batch.json", json_data.encode("utf-8"), content_type="application/json")
    batch = UploadedEvaluationBatch.objects.create(name="exp_test", json_file=json_file)

    from django.contrib.admin.sites import AdminSite

    from app.admin import UploadedEvaluationBatchAdmin
    admin_instance = UploadedEvaluationBatchAdmin(UploadedEvaluationBatch, AdminSite())
    request = client.request().wsgi_request
    form = None

    admin_instance.save_model(request, batch, form, change=False)

    assert Evaluation.objects.filter(exp_id="exp_test").count() == 1


@pytest.mark.django_db
def test_uploaded_test_paper_creates_questions_and_scores(client):
    csv_content = (
        "question_id,question,standard_answer,difficulty,source,tags\n"
        "q1,What is AI?,Artificial Intelligence,3,Mock,AI\n"
    )
    csv_file = SimpleUploadedFile("paper.csv", csv_content.encode("utf-8"), content_type="text/csv")
    paper = UploadedTestPaper.objects.create(name="test_paper", csv_file=csv_file)

    from django.contrib.admin.sites import AdminSite

    from app.admin import UploadedTestPaperAdmin
    admin_instance = UploadedTestPaperAdmin(UploadedTestPaper, AdminSite())
    request = client.request().wsgi_request
    form = None

    admin_instance.save_model(request, paper, form, change=False)

    assert ExamPaperQuestion.objects.filter(test_paper=paper).count() == 1
    assert Evaluation.objects.filter(exp_id="test_paper").count() == 1


@pytest.mark.django_db
def test_exam_paper_question(client):
    """Test the ExamPaperQuestion view to ensure it returns a CSV response with the correct content."""
    url = reverse("ExamPaperQuestion")
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    content = response.content.decode("utf-8")
    assert "question" in content
    assert "standard_answer" in content
