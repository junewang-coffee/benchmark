# api.py
import csv
import hashlib
import json
import uuid

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from ninja import File, NinjaAPI, Schema
from ninja.files import UploadedFile

from .models import Evaluation, StandardAnswer

api = NinjaAPI()

class EvaluationRequest(Schema):
    test_project_id: str
    question_id: str | None = None
    test_question: str
    question_source: str
    bot_response: str

class EvaluationResponse(Schema):
    question_id: str
    test_project_id: str
    test_question: str
    bot_response: str
    question_source: str
    standard_answer: str
    difficulty: int
    accuracy: int
    relevance: int
    logic: int
    conciseness: int
    language_quality: int
    total_score: int

def generate_question_id() -> str:
    random_string = str(uuid.uuid4())
    return hashlib.md5(random_string.encode()).hexdigest()[:6]

def evaluate_response(bot_response: str, standard_answer: str) -> dict[str, int]:
    accuracy = 5 if standard_answer in bot_response else 3
    relevance = logic = conciseness = language_quality = 4
    total_score = sum([accuracy, relevance, logic, conciseness, language_quality])
    return {
        "accuracy": accuracy,
        "relevance": relevance,
        "logic": logic,
        "conciseness": conciseness,
        "language_quality": language_quality,
        "total_score": total_score
    }

@api.post("/evaluate", response=EvaluationResponse)
def evaluate(request, data: EvaluationRequest):
    question_id = data.question_id or generate_question_id()
    try:
        standard_answer_obj = StandardAnswer.objects.get(source=data.question_source)
    except StandardAnswer.DoesNotExist:
        raise Http404(f"\u627e\u4e0d\u5230\u6a19\u6e96\u7b54\u6848\uff0c\u4f86\u6e90: {data.question_source}")

    result = evaluate_response(data.bot_response, standard_answer_obj.content)
    difficulty = 3

    Evaluation.objects.create(
        question_id=question_id,
        test_project_id=data.test_project_id,
        test_question=data.test_question,
        bot_response=data.bot_response,
        question_source=data.question_source,
        standard_answer=standard_answer_obj.content,
        difficulty=difficulty,
        **result
    )

    return EvaluationResponse(
        question_id=question_id,
        test_project_id=data.test_project_id,
        test_question=data.test_question,
        bot_response=data.bot_response,
        question_source=data.question_source,
        standard_answer=standard_answer_obj.content,
        difficulty=difficulty,
        **result
    )

@api.post("/evaluate/batch", response=list[EvaluationResponse])
def batch_evaluate(request, data: list[EvaluationRequest]):
    return [evaluate(request, item) for item in data]

@api.get("/evaluations", response=dict[str, EvaluationResponse])
def get_all_evaluations(request):
    evaluations = Evaluation.objects.all()
    return {eval.question_id: EvaluationResponse(**eval.__dict__) for eval in evaluations}

@api.get("/evaluation/{question_id}", response=EvaluationResponse)
def get_evaluation(request, question_id: str):
    evaluation = get_object_or_404(Evaluation, question_id=question_id)
    return EvaluationResponse(**evaluation.__dict__)

@api.get("/project/{project_id}/evaluations", response=list[EvaluationResponse])
def get_project_evaluations(request, project_id: str):
    evaluations = Evaluation.objects.filter(test_project_id=project_id)
    return [EvaluationResponse(**eval.__dict__) for eval in evaluations]

@api.get("/project/{project_id}/export_csv")
def export_project_csv(request, project_id: str):
    evaluations = Evaluation.objects.filter(test_project_id=project_id)
    if not evaluations.exists():
        raise Http404(f"\u627e\u4e0d\u5230\u6e2c\u8a66\u9805\u76ee {project_id} \u7684\u8cc7\u6599")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="project_{project_id}_evaluations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'question_id', 'test_project_id', 'test_question', 'bot_response',
        'question_source', 'standard_answer', 'difficulty',
        'accuracy', 'relevance', 'logic', 'conciseness', 'language_quality',
        'total_score', 'created_at'
    ])

    for eval in evaluations:
        writer.writerow([
            eval.question_id,
            eval.test_project_id,
            eval.test_question,
            eval.bot_response,
            eval.question_source,
            eval.standard_answer,
            eval.difficulty,
            eval.accuracy,
            eval.relevance,
            eval.logic,
            eval.conciseness,
            eval.language_quality,
            eval.total_score,
            eval.created_at.isoformat()
        ])

    return response


@api.post("/upload_json", response=list[dict[str, str]])
def upload_json(request, file: UploadedFile = File(...), project_id: str | None = None):
    try:
        raw = file.read().decode("utf-8")
        data = json.loads(raw)
    except Exception as e:
        raise Http404(f"無法解析 JSON 檔案：{e}")

    results = []
    for item in data:
        question_id = item.get("question_id") or generate_question_id()
        question = item.get("question")
        response = item.get("response")
        sources = item.get("sources", [])

        if not (question and response and sources):
            continue  # 跳過不完整資料

        source_title = sources[0].get("title", "")
        reference = sources[0].get("content", "")

        try:
            standard_answer_obj = StandardAnswer.objects.get(source=source_title)
            standard_answer = standard_answer_obj.content
        except StandardAnswer.DoesNotExist:
            standard_answer = reference  # fallback 使用 sources 裡提供的內容

        score = evaluate_response(response, standard_answer)

        Evaluation.objects.update_or_create(
            question_id=question_id,
            defaults={
                "test_project_id": project_id or "uploaded_project",
                "test_question": question,
                "bot_response": response,
                "question_source": source_title,
                "standard_answer": standard_answer,
                "difficulty": 3,
                **score
            }
        )

        results.append({
            "question_id": question_id,
            "total_score": str(score["total_score"])
        })

    return results
