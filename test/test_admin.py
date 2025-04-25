import csv
import json
from io import StringIO

import pytest
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.test import Client
from django.urls import reverse

from app.admin import UploadedTestPaperAdmin
from app.models import TestPaperQuestion, UploadedTestPaper


@pytest.fixture
def uploaded_test_paper(db):
    """Fixture to create a sample UploadedTestPaper object."""
    test_paper = UploadedTestPaper.objects.create(
        name="Sample Test Paper",
        csv_file="uploads/sample_test_paper.csv",
    )
    return test_paper


@pytest.fixture
def admin_instance():
    """Fixture to create an instance of UploadedTestPaperAdmin."""
    return UploadedTestPaperAdmin(UploadedTestPaper, AdminSite())


@pytest.fixture
def mock_csv_file(settings, tmpdir):
    """Fixture to create a temporary CSV file."""
    csv_content = """question_id,question,standard_answer,difficulty,source,tags
Q001,What is the capital of France?,Paris,3,Midterm A,geography
Q002,Who wrote Hamlet?,William Shakespeare,3,Midterm A,literature
"""
    file_path = tmpdir.join("sample_test_paper.csv")
    file_path.write(csv_content)
    settings.MEDIA_ROOT = tmpdir
    return file_path


def test_export_selected_papers_as_student_template(admin_instance, uploaded_test_paper):
    """Test exporting selected test papers as a JSON template."""
    request = HttpRequest()
    queryset = UploadedTestPaper.objects.filter(id=uploaded_test_paper.id)

    response = admin_instance.export_selected_papers_as_student_template(request, queryset)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response["Content-Disposition"] == 'attachment; filename="student_test_paper_template.json"'

    data = json.loads(response.content)
    assert isinstance(data, list)
    assert all("question_id" in item and "question" in item for item in data)


def test_save_model(admin_instance, mock_csv_file, db):
    """Test saving a model and processing its associated CSV file."""
    request = HttpRequest()
    obj = UploadedTestPaper(name="Test Paper", csv_file=mock_csv_file)
    form = None
    change = False

    admin_instance.save_model(request, obj, form, change)

    # Verify that questions were created
    questions = TestPaperQuestion.objects.filter(test_paper=obj)
    assert questions.count() == 2
    assert questions.filter(question_id="Q001", question="What is the capital of France?").exists()
    assert questions.filter(question_id="Q002", question="Who wrote Hamlet?").exists()


def test_download_button(admin_instance, uploaded_test_paper):
    """Test the download button generates the correct URL."""
    button_html = admin_instance.download_button(uploaded_test_paper)
    expected_url = reverse("download_test_paper", args=[uploaded_test_paper.id])

    assert expected_url in button_html
    assert "Download Test Paper" in button_html


def test_download_selected_papers(admin_instance, uploaded_test_paper):
    """Test downloading selected test papers as a CSV file."""
    request = HttpRequest()
    queryset = UploadedTestPaper.objects.filter(id=uploaded_test_paper.id)

    response = admin_instance.download_selected_papers(request, queryset)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == 'attachment; filename="selected_test_papers.csv"'

    content = response.content.decode("utf-8")
    reader = csv.reader(StringIO(content))
    rows = list(reader)

    assert rows[0] == ["Test Paper Name", "Uploaded At", "File Path"]
    assert rows[1][0] == uploaded_test_paper.name