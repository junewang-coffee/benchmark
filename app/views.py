# views.py
import csv

from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Evaluation, UploadedTestPaper


def dashboard(request):
    projects = Evaluation.objects.values('test_project_id').annotate(
        avg_score=Avg('total_score'),
        count=Count('question_id')
    ).order_by('test_project_id')

    return render(request, 'dashboard.html', {'projects': projects})



def download_test_paper(request, paper_id):
    """下載指定的試卷"""
    paper = get_object_or_404(UploadedTestPaper, id=paper_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{paper.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(['question', 'standard_answer', 'difficulty', 'source', 'tags'])

    for question in paper.questions.all():
        writer.writerow([
            question.question,
            question.standard_answer,
            question.difficulty,
            question.source,
            question.tags,
        ])

    return response
