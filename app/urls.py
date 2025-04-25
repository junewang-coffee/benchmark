from django.urls import path

from app.admin import download_csv_template
from app.api import api  # 你原本用 Ninja 寫的 API
from app.views import download_test_paper

urlpatterns = [
    path("", api.urls),  # 將 NinjaAPI 掛在這個 app 下
    path('admin/download-csv-template/', download_csv_template, name='download_csv_template'),
    path('admin/download-test-paper/<int:paper_id>/', download_test_paper, name='download_test_paper'),
]
