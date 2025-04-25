# models.py
from django.db import models


class StandardAnswer(models.Model):
    source = models.CharField(max_length=255, unique=True)
    content = models.TextField()

class TestQuestion(models.Model):
    question_id = models.CharField(max_length=10, unique=True)
    question = models.TextField()
    standard_answer = models.TextField()
    difficulty = models.IntegerField(default=3)
    source = models.CharField(max_length=255)
    tags = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"[{self.question_id}] {self.question[:30]}"

class UploadedTestPaper(models.Model):
    name = models.CharField(max_length=100)  # 試卷名稱
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 上傳時間
    csv_file = models.FileField(upload_to='uploads/')  # 試卷檔案

    def __str__(self):
        return self.name

class Evaluation(models.Model):
    exp_id = models.CharField(max_length=50)  # 實驗 ID
    test_paper_id = models.CharField(max_length=50, blank=True)  # 試卷 ID
    question_id = models.CharField(max_length=10)  # 問題 ID，允許重複
    test_question = models.TextField()
    bot_response = models.TextField()
    question_source = models.CharField(max_length=255)
    standard_answer = models.TextField()
    difficulty = models.IntegerField()
    accuracy = models.IntegerField()
    relevance = models.IntegerField()
    logic = models.IntegerField()
    conciseness = models.IntegerField()
    language_quality = models.IntegerField()
    total_score = models.IntegerField()
    overall_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("exp_id", "question_id")  # 確保同一實驗內 question_id 唯一
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

    def __str__(self):
        return f"{self.exp_id} - {self.question_id}"


class UploadedEvaluationBatch(models.Model):
    name = models.CharField(max_length=100)
    json_file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        uploaded_at_str = self.uploaded_at.strftime('%Y-%m-%d') if self.uploaded_at else "未定義"
        return f"{self.name} ({uploaded_at_str})"
class TestPaperQuestion(models.Model):
    test_paper = models.ForeignKey(
        UploadedTestPaper, on_delete=models.CASCADE, related_name="questions"
    )
    question_id = models.CharField(max_length=10, blank=True)  # 移除 unique=True，允許重複
    question = models.TextField()
    standard_answer = models.TextField()
    difficulty = models.IntegerField(default=3)
    source = models.CharField(max_length=255, blank=True)
    tags = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.question[:50]}..."
