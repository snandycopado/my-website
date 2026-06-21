import os
import json
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


class GenerateRequest(BaseModel):
    student_class: int


class SubmitRequest(BaseModel):
    student_class: int
    questions: list
    answers: dict


@app.get("/")
def home():
    return {"message": "Hello from Python!"}


@app.get("/data")
def get_data():
    return {"items": ["Apple", "Banana", "Cherry"], "count": 3}


@app.post("/api/generate-questions")
def generate_questions(req: GenerateRequest):
    prompt = f"""Generate exactly 10 English language questions for Class {req.student_class} students.

Return ONLY a JSON array with exactly 10 objects. Each object must have:
- "id": number (1-10)
- "question": the question text
- "options": array of exactly 4 answer choices labeled A, B, C, D
- "correct_answer": the correct option letter (A, B, C, or D)

Questions should be age-appropriate for Class {req.student_class} and cover grammar, vocabulary, sentence formation, and reading comprehension.

Return ONLY valid JSON, no markdown, no explanation."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        questions = json.loads(text)
        questions_without_answers = []
        for q in questions:
            questions_without_answers.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
            })
        return {
            "questions": questions_without_answers,
            "_answer_key": questions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/submit-answers")
def submit_answers(req: SubmitRequest):
    questions_text = json.dumps(req.questions, indent=2)
    answers_text = json.dumps(req.answers, indent=2)

    prompt = f"""You are grading an English test for a Class {req.student_class} student.

Here are the questions with correct answers:
{questions_text}

Here are the student's answers (question id -> selected option letter):
{answers_text}

Evaluate each answer. Return ONLY a JSON object with:
- "score": number of correct answers out of 10
- "total": 10
- "percentage": score percentage
- "results": array of 10 objects, each with:
  - "id": question id
  - "question": the question text
  - "student_answer": what the student chose
  - "correct_answer": the correct answer
  - "is_correct": boolean

Return ONLY valid JSON, no markdown, no explanation."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
