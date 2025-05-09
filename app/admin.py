import csv
import json
import re
import uuid
from io import TextIOWrapper
from typing import ClassVar

from django.contrib import admin, messages
from django.db import connection
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from app.models import (
    Evaluation,
    ExamPaperQuestion,
    StandardAnswer,
    TestQuestion,
    UploadedEvaluationBatch,
    UploadedTestPaper,
)
from app.openai_eval import score_response


def enable_wal():
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")

def format_json_as_plain_text(json_data: list[dict]) -> str:
    r"""將 JSON 格式的 list of dict 轉換為以換行和縮排區分的純文本，並移除特殊符號。.

    Parameters
    ----------
    json_data : list[dict]
        要格式化的 JSON 數據。

    Returns:
    -------
    str
        格式化後的純文本 移除了 \n、\s、\t 等符號。
    """
    # 將 JSON 格式化為帶縮排的字符串
    try:
        formatted_text = json.dumps(json_data, ensure_ascii=False, indent=4)
        # 移除 \n、\s、\t 等特殊符號
        cleaned_text = re.sub(r"[\n\t\r]", " ", formatted_text)
        return re.sub(r"\s{2,}", " ", cleaned_text)  # 移除多餘的空格
    except json.JSONDecodeError:
        return "Invalid JSON data"
    except:  # noqa: E722
        return ""

def generate_unique_uuid_question_id():
    while True:
        question_id = uuid.uuid4().hex[:8]
        if not TestQuestion.objects.filter(question_id=question_id).exists():
            return question_id

# Utility Functions

def save_evaluation(evaluation_data: dict):
    """Save evaluation results."""
    Evaluation.objects.create(
        exp_id=evaluation_data["exp_id"],
        test_paper_id=evaluation_data["test_paper_id"],
        question_id=evaluation_data["question_id"],
        test_question=evaluation_data["question"],
        bot_response=evaluation_data["response"],
        question_source=evaluation_data["question_source"],
        standard_answer=evaluation_data["standard_answer"],
        difficulty=3,
        accuracy=evaluation_data["scores"].get("accuracy"),
        relevance=evaluation_data["scores"].get("relevance"),
        logic=evaluation_data["scores"].get("logic"),
        conciseness=evaluation_data["scores"].get("conciseness"),
        language_quality=evaluation_data["scores"].get("language_quality"),
        total_score=evaluation_data["scores"].get("total_score"),
        overall_comment=evaluation_data["scores"].get("overall_comment"),
    )


def download_exam_paper_question(request: HttpRequest):  # noqa: ARG001
    """Download a CSV template for exam paper questions."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="exam_paper_question_template.csv"'

    writer = csv.writer(response)
    writer.writerow(["question", "standard_answer", "difficulty", "source", "tags"])
    writer.writerow(["What is the fcapital of France?", "Paris", 3, "Midterm A", "geography"])
    writer.writerow(["Who wrote Hamlet?", "William Shakespeare", 3, "Midterm A", "literature"])
    return response


def download_test_paper(request: HttpRequest, paper_id:str):
    """Handles the download of a specific test paper as a CSV file.

    Args:
        request (HttpRequest): The HTTP request object.
        paper_id (str): The unique identifier of the test paper to be downloaded.

    Returns:
        HttpResponse: A response object containing the CSV file as an attachment.

    Raises:
        Http404: If the test paper with the given ID does not exist.
    """
    _ = request
    paper = get_object_or_404(UploadedTestPaper, id=paper_id)
    with paper.csv_file.open("rb") as f:
        response = HttpResponse(f.read(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{paper.name}.csv"'
        return response


# Admin Classes
class ExamPaperQuestionInline(admin.TabularInline):
    """Inline admin interface for managing test paper questions.

    This class allows adding, editing, and viewing questions associated with a test paper
    directly within the admin interface for the test paper model.
    """
    model = ExamPaperQuestion
    extra = 1
    readonly_fields = ("question_id", "question", "standard_answer", "difficulty", "source", "tags")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """EvaluationAdmin is a Django ModelAdmin class for managing the Evaluation model in the admin interface.

    Attributes:
        list_display (tuple): Specifies the fields to display in the list view of the admin interface.
        list_filter (tuple): Specifies the fields to filter by in the admin interface.
        search_fields (tuple): Specifies the fields to include in the search functionality.
        actions (list): Specifies the custom actions available in the admin interface.

    Methods:
        export_selected_to_csv(request, queryset):
            Exports the selected Evaluation objects to a CSV file.

    Args:
                request (HttpRequest): The HTTP request object.
                queryset (QuerySet): The queryset of selected Evaluation objects.

    Returns:
                HttpResponse: A response containing the CSV file for download.
    """
    list_display = (
        "exp_id",
        "question_id",
        "test_question",
        "question_source",
        "total_score",
        "created_at",
    )
    list_filter = ("exp_id", "question_source", "created_at")
    search_fields = ("question_id", "exp_id")
    from typing import ClassVar

    actions: ClassVar[list[str]] = ["export_selected_to_csv"]

    @admin.action(description="Export selected evaluations to CSV")
    def export_selected_to_csv(self, request: HttpRequest, queryset: QuerySet):
        """Export the selected Evaluation objects to a CSV file.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The queryset of selected Evaluation objects.

        Returns:
        -------
        HttpResponse
            A response containing the CSV file for download.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="evaluations_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "question_id",
                "exp_id",
                "test_paper_id",
                "test_question",
                "bot_response",
                "question_source",
                "standard_answer",
                "difficulty",
                "accuracy",
                "relevance",
                "logic",
                "conciseness",
                "language_quality",
                "total_score",
                "created_at",
            ]
        )

        for evaluation in queryset:
            writer.writerow(
                [
                    evaluation.question_id,
                    evaluation.exp_id,
                    evaluation.test_paper_id,
                    evaluation.test_question,
                    evaluation.bot_response,
                    evaluation.question_source,
                    evaluation.standard_answer,
                    evaluation.difficulty,
                    evaluation.accuracy,
                    evaluation.relevance,
                    evaluation.logic,
                    evaluation.conciseness,
                    evaluation.language_quality,
                    evaluation.total_score,
                    evaluation.created_at.isoformat(),
                ]
            )

        return response


@admin.register(StandardAnswer)
class StandardAnswerAdmin(admin.ModelAdmin):
    """StandardAnswerAdmin is a custom ModelAdmin class for managing the StandardAnswer model in the Django admin interface.

    Attributes:
        list_display (tuple): Specifies the fields to display in the admin list view.
        search_fields (tuple): Specifies the fields to include in the search functionality.

    Methods:
        has_module_permission(request):
            Overrides the default method to restrict access to the module in the admin interface.
            Returns False to indicate that the module is not accessible.
    """
    list_display = ("source", "content")
    search_fields = ("source",)

    def has_module_permission(self, request: HttpRequest) -> bool:
        """Determine if the module is accessible in the admin interface.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.

        Returns:
        -------
        bool
            False, indicating that the module is not accessible.
        """
        # Using the request argument to avoid it being marked as unused
        _ = request
        return False

# @admin.register(UploadedEvaluationBatch)
# class UploadedEvaluationBatchAdmin(admin.ModelAdmin):
#     """Admin interface for managing uploaded evaluation batches.

#     This class provides functionality to save and process evaluation batches,
#     ensuring that duplicate experiment IDs are not allowed and evaluations are
#     created based on the uploaded JSON data.
#     """

#     change_form_template = "admin/uploaded_evaluation_batch_change_form.html"  # 自定義模板
#     list_display = ("name", "uploaded_at", "json_file_link")
#     readonly_fields = ("json_file_link",)

#     def json_file_link(self, obj):
#         """Provide a link to download the uploaded JSON file."""
#         if obj.json_file:
#             return mark_safe(f'<a href="{obj.json_file.url}" download>{obj.json_file.name}</a>')
#         return "-"
#     json_file_link.short_description = "Uploaded JSON File"

#     def save_model(self, request: HttpRequest, obj: UploadedEvaluationBatch, form: ModelForm, change: bool):
#         """Save the model instance and process related data.

#         Parameters
#         ----------
#         request : HttpRequest
#             The HTTP request object.
#         obj : UploadedEvaluationBatch
#             The model instance being saved.
#         form : ModelForm
#             The form used to save the instance.
#         change : bool
#             True if the instance is being changed, False if it's being created.
#         """
#         if Evaluation.objects.filter(exp_id=obj.name).exists():
#             self.message_user(
#                 request,
#                 f"Experiment ID '{obj.name}' already exists. Cannot add duplicate.",
#                 level=messages.WARNING,
#             )
#             return

#         super().save_model(request, obj, form, change)

#         raw = obj.json_file.open("rb").read().decode("utf-8")
#         data = json.loads(raw)

#         for idx, item in enumerate(data, start=1):
#             print(f"Processing item {idx}...")  # noqa: T201

#             question_id = item.get("question_id")
#             question = item.get("question")
#             response = item.get("response")
#             question_source = item.get("sources", "")  # 獲取 source 資料
            

#             # 根據 question_id 從資料庫篩選出對應的 standard_answer
#             try:
#                 exam_question = ExamPaperQuestion.objects.get(question_id=question_id)
#                 standard_answer = exam_question.standard_answer
#             except ExamPaperQuestion.DoesNotExist:
#                 self.message_user(
#                     request,
#                     f"Skipping item {idx}: Question ID '{question_id}' not found in ExamPaperQuestion.",
#                     level=messages.WARNING,
#                 )
#                 continue

#             if not all([question_id, question, response, standard_answer]):
#                 self.message_user(
#                     request,
#                     f"Skipping item {idx}: Missing required fields.",
#                     level=messages.WARNING,
#                 )
#                 continue

#             # 使用 source 傳遞給 score_response
#             scores = score_response(question, response, standard_answer, question_source)

#             save_evaluation({
#                 "exp_id": obj.name,
#                 "test_paper_id": obj.id,
#                 "question_id": question_id,
#                 "question": question,
#                 "response": response,
#                 "standard_answer": standard_answer,
#                 "question_source": "",
#                 "scores": scores,
#             })

@admin.register(UploadedEvaluationBatch)
class UploadedEvaluationBatchAdmin(admin.ModelAdmin):
    """Admin interface for managing uploaded evaluation batches.

    This class provides functionality to save and process evaluation batches,
    ensuring that duplicate experiment IDs are not allowed and evaluations are
    created based on the uploaded JSON or CSV data.
    """

    change_form_template = "admin/uploaded_evaluation_batch_change_form.html"  # 自定義模板
    list_display = ("name", "uploaded_at", "json_file_link")
    readonly_fields = ("json_file_link",)

    def json_file_link(self, obj):
        """Provide a link to download the uploaded file."""
        if obj.json_file:
            return mark_safe(f'<a href="{obj.json_file.url}" download>{obj.json_file.name}</a>')
        return "-"
    json_file_link.short_description = "Uploaded File"

    def save_model(self, request: HttpRequest, obj: UploadedEvaluationBatch, form: ModelForm, change: bool):
        """Save the model instance and process related data.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        obj : UploadedEvaluationBatch
            The model instance being saved.
        form : ModelForm
            The form used to save the instance.
        change : bool
            True if the instance is being changed, False if it's being created.
        """
        if Evaluation.objects.filter(exp_id=obj.name).exists():
            self.message_user(
                request,
                f"Experiment ID '{obj.name}' already exists. Cannot add duplicate.",
                level=messages.WARNING,
            )
            return

        super().save_model(request, obj, form, change)

        # 打開文件並自動識別格式
        raw = obj.json_file.open("rb").read().decode("utf-8")
        if obj.json_file.name.endswith(".json"):
            data = json.loads(raw)  # 處理 JSON 文件
        elif obj.json_file.name.endswith(".csv"):
            data = self.parse_csv(raw)  # 處理 CSV 文件
        else:
            self.message_user(
                request,
                "Unsupported file format. Please upload a JSON or CSV file.",
                level=messages.ERROR,
            )
            return

        # 處理數據
        for idx, item in enumerate(data, start=1):
            print(f"Processing item {idx}...")  # noqa: T201

            question_id = item.get("question_id")
            question = item.get("question")
            response = item.get("response", "")
            question_source = item.get("sources", "")  # 獲取 source 資料

            # 根據 question_id 從資料庫篩選出對應的 standard_answer
            try:
                exam_question = ExamPaperQuestion.objects.get(question_id=question_id)
                standard_answer = exam_question.standard_answer
            except ExamPaperQuestion.DoesNotExist:
                self.message_user(
                    request,
                    f"Skipping item {idx}: Question ID '{question_id}' not found in ExamPaperQuestion.",
                    level=messages.WARNING,
                )
                continue

            if not all([question_id, question, standard_answer]):
                self.message_user(
                    request,
                    f"Skipping item {idx}: Missing required fields.",
                    level=messages.WARNING,
                )
                continue

            # 使用 source 傳遞給 score_response
            scores = score_response(question, response, standard_answer, question_source)

            save_evaluation({
                "exp_id": obj.name,
                "test_paper_id": obj.id,
                "question_id": question_id,
                "question": question,
                "response": response,
                "standard_answer": standard_answer,
                "question_source": question_source,
                "scores": scores,
            })

    def parse_csv(self, raw: str) -> list[dict]:
        """Parse CSV content into a list of dictionaries.

        Parameters
        ----------
        raw : str
            The raw CSV content as a string.

        Returns
        -------
        list[dict]
            A list of dictionaries representing the CSV rows.
        """
        import csv
        from io import StringIO

        csv_data = StringIO(raw)
        reader = csv.DictReader(csv_data)
        return [row for row in reader]
@admin.register(UploadedTestPaper)
class UploadedTestPaperAdmin(admin.ModelAdmin):
    """Admin interface for managing UploadedTestPaper objects.

    This class provides customizations for the Django admin interface, including:
    - Displaying specific fields in the admin list view.
    - Adding search functionality for the "name" field.
    - Defining custom actions for exporting and downloading test papers.
    - Handling the saving of UploadedTestPaper objects and processing associated CSV files.
    - Generating a download button for test papers in the admin interface.
    """

    list_display = ("name", "uploaded_at", "download_button")
    search_fields = ("name",)
    actions: ClassVar[list[str]] = ["download_selected_papers", "export_as_csv", "export_as_json"]
    inlines: ClassVar[list] = [ExamPaperQuestionInline]


    @admin.action(description="Export student exam as CSV")
    def export_as_csv(self, request: HttpRequest, queryset: QuerySet):
        """Export selected Exam  papers as a CSV template."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="student_test_paper_template.csv"'

        writer = csv.writer(response)
        writer.writerow(["question_id", "question", "response", "source"])  # CSV 標題
        for paper in queryset:
            for question in paper.questions.all():
                writer.writerow([question.question_id, question.question, "", ""])

        return response

    @admin.action(description="Export student exam as JSON")
    def export_as_json(self, request: HttpRequest, queryset: QuerySet):
        """Export selected test papers as a JSON template."""
        _  = request
        result = [
            {
                "question_id": question.question_id,
                "question": question.question,
                "response": "",
                "source": "",
            }
            for paper in queryset
            for question in paper.questions.all()
        ]

        response = HttpResponse(
            json.dumps(result, ensure_ascii=False, indent=4),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="student_test_paper_template.json"'

        return response

    def save_model(self, request: HttpRequest, obj: UploadedTestPaper, form: ModelForm, change: bool):
        """Save the UploadedTestPaper object and process its associated CSV file."""
        super().save_model(request, obj, form, change)

        with obj.csv_file.open("rb") as file:
            csv_file = TextIOWrapper(file, encoding="utf-8")
            reader = csv.DictReader(csv_file)

            for idx, row in enumerate(reader, start=1):
                # 1. 自動產生 question_id
                question_id = generate_unique_uuid_question_id()

                # 2. 建立題目
                ExamPaperQuestion.objects.create(
                    test_paper=obj,
                    question_id=question_id,
                    question=row["question"],
                    standard_answer=row["standard_answer"],
                    difficulty=int(row["difficulty"]),
                    source=row["source"],
                    tags=row["tags"],
                )

                # 3. 空白回應自動評分
                response = ""
                reference = row["standard_answer"]
                scores = ""
                # 4. 儲存評估紀錄
                save_evaluation({
                    "exp_id": obj.name,
                    "test_paper_id": obj.id,
                    "question_id": question_id,
                    "question": row["question"],
                    "response": response,
                    "reference": reference,
                    "scores": scores,
                })

    def download_button(self, obj: UploadedTestPaper):
        """Generate a download button for the test paper.

        Parameters
        ----------
        obj : UploadedTestPaper
            The test paper object for which the download button is generated.

        Returns:
        -------
        str
            An HTML string for the download button.
        """
        url = reverse("download_test_paper", args=[obj.id])
        return format_html('<a class="button" href="{}">Download Test Paper</a>', url)

    download_button.short_description = "Download Test Paper"

    @admin.action(description="Download selected test papers")
    def download_selected_papers(self, _: HttpRequest, queryset: QuerySet):
        """Download the selected test papers as a CSV file.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The queryset of selected UploadedTestPaper objects.

        Returns:
        -------
        HttpResponse
            A CSV response containing the selected test papers.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="selected_test_papers.csv"'

        writer = csv.writer(response)
        writer.writerow(["Test Paper Name", "Uploaded At", "File Path"])

        for paper in queryset:
            writer.writerow([paper.name, paper.uploaded_at, paper.csv_file.url])

        return response
