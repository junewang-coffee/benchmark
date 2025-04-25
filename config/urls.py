# config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("app.urls")),  # ✅ 將 app 中的路由掛載進來
]
