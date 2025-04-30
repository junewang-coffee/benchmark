from django.urls import path

from app.admin import ExamPaperQuestion
from app.api import api  # 你原本用 Ninja 寫的 API
from app.views import download_test_paper

urlpatterns = [
    path("", api.urls),  # 將 NinjaAPI 掛在這個 app 下
    path('admin/download-csv-template/', ExamPaperQuestion, name='ExamPaperQuestion'),
    path('admin/download-test-paper/<int:paper_id>/', download_test_paper, name='download_test_paper'),
]
