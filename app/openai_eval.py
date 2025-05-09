import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # ✅ 載入 .env 檔案中的環境變數

client = OpenAI()  # 自動讀取 OPENAI_API_KEY 環境變數

def score_response(question: str, response: str, standard_answer: str, source: str) -> dict[str, Any]:
    """Score a student's response based on predefined criteria, including source.

    Parameters
    ----------
    question : str
        The question text.
    response : str
        The student's response.
    standard_answer : str
        The reference answer.
    source : str
        The source content.

    Returns:
    -------
    Dict[str, Any]
        A dictionary containing scores for various criteria and an overall comment.
    """
    prompt = f"""
你是一個教育評分專家,請針對學生的回答進行以下五個面向的評分:
1. 準確度 accuracy
2. 相關 relevance
3. 邏輯性 logic
4. 簡潔度 conciseness
5. 語言表現 language_quality

題目:{question}
標準答案:{standard_answer}
參考資料:{source}
學生回答:{response}

其中,參考資料是用來幫助學生回答問題的,但不一定要完全依賴它。但如果參考資料跟答案不一致,請對學生答案進行扣分。
請針對每一個項目以 1 到 5 分進行打分,並給出總分(total_score),以及綜合評價的簡要說明,輸出格式如下:
{{
  "accuracy": x,
  "relevance": x,
  "logic": x,
  "conciseness": x,
  "language_quality": x,
  "total_score": x,
  "overall_comment": "簡要說明"
}}
    """.strip()

    chat_response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "你是一個精確的教育評分助理。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    # 解析回傳內容
    content = chat_response.choices[0].message.content
    try:
        content_load = json.loads(content)
    except Exception as e:
        return {
            "accuracy": 0,
            "relevance": 0,
            "logic": 0,
            "conciseness": 0,
            "language_quality": 0,
            "total_score": 0,
            "overall_comment": "",
            "error": str(e),
            "raw_response": content
        }
    content_load['total_score'] = sum([
        content_load["accuracy"],
        content_load["relevance"],
        content_load["logic"],
        content_load["conciseness"],
        content_load["language_quality"]
    ])
    return content_load


# def score_response(question: str, response: str, reference: str) -> dict[str, Any]:
#     """Score a student's response based on predefined criteria.

#     Parameters
#     ----------
#     question : str
#         The question text.
#     response : str
#         The student's response.
#     reference : str
#         The reference answer.

#     Returns:
#     -------
#     Dict[str, Any]
#         A dictionary containing scores for various criteria and an overall comment.
#     """
#     prompt = f"""
# 你是一個教育評分專家,請針對學生的回答進行以下五個面向的評分:
# 1. 準確度 accuracy
# 2. 相關 relevance
# 3. 邏輯性 logic
# 4. 簡潔度 conciseness
# 5. 語言表現 language_quality

# 題目:{question}
# 標準答案:{reference}
# 學生回答:{response}

# 請針對每一個項目以 1 到 5 分進行打分,並給出總分(total_score),以及綜合評價的簡要說明,輸出格式如下:
# {{
#   "accuracy": x,
#   "relevance": x,
#   "logic": x,
#   "conciseness": x,
#   "language_quality": x,
#   "total_score": x,
#   "overall_comment": "簡要說明"
# }}
#     """.strip()

#     chat_response = client.chat.completions.create(
#         model="gpt-4.1-nano",
#         messages=[
#             {"role": "system", "content": "你是一個精確的教育評分助理。"},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0
#     )

#     # 解析回傳內容
#     content = chat_response.choices[0].message.content
#     try:
#         content_load = json.loads(content)
#     except Exception as e:
#         return {
#             "accuracy": 0,
#             "relevance": 0,
#             "logic": 0,
#             "conciseness": 0,
#             "language_quality": 0,
#             "total_score": 0,
#             "overall_comment": "",
#             "error": str(e),
#             "raw_response": content
#         }
#     content_load['total_score'] = sum([content_load["accuracy"],
#                                             content_load["relevance"],
#                                               content_load["logic"],
#                                                 content_load["conciseness"],
#                                                   content_load["language_quality"]])
#     # content_load['total_score'] = round(content_load['total_score'] / 5, 2)  # 平均分數
#     content_load['total_score'] = content_load['total_score']
#     return content_load

# def evaluate_json_file(json_path: str) -> list[dict[str, Any]]:
#     """Evaluate responses from a JSON file.

#     Parameters
#     ----------
#     json_path : str
#         The path to the JSON file containing the data.

#     Returns:
#     -------
#     List[Dict[str, Any]]
#         A list of dictionaries containing evaluation results.
#     """
#     with Path(json_path).open(encoding="utf-8") as f:
#         data = json.load(f)

#     results = []
#     for item in data:
#         question_id = item.get("question_id")
#         question = item.get("question")
#         response = item.get("response")

#         # 自動萃取第一筆 source 作為標準答案（你也可以改用 AI 萃取）  # noqa: RUF003
#         first_source = item.get("sources", [])
#         reference = first_source[0]["content"] if first_source else ""

#         # 如果資料不完整就跳過
#         if not all([question_id, question, response, reference]):
#             continue

#         # 用 OpenAI 評分
#         scores = score_response(question, response, reference)
#         scores.update({
#             "question_id": question_id,
#             "question": question,
#             "response": response,
#             "reference": reference,
#             "overall_comment": scores.get("overall_comment", "")  # 確保包含綜合評價
#         })
#         results.append(scores)

#     return results
