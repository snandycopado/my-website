import os
import json
import anthropic
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
TOPICS_FILE = os.path.join(UPLOAD_DIR, "topics.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_topics(topics):
    with open(TOPICS_FILE, "w") as f:
        json.dump(topics, f, indent=2)


def read_file_content(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


class GenerateRequest(BaseModel):
    student_class: int


class SubmitRequest(BaseModel):
    student_class: int
    questions: list
    answers: dict


class CustomSubmitRequest(BaseModel):
    topic_name: str
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


# --- Custom Online Test Endpoints ---

@app.post("/api/upload-topic")
async def upload_topic(
    topic_name: str = Form(...),
    files: list[UploadFile] = File(...),
):
    safe_name = topic_name.strip().replace(" ", "_").lower()
    topic_dir = os.path.join(UPLOAD_DIR, safe_name)
    os.makedirs(topic_dir, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = os.path.join(topic_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        saved_files.append(file.filename)

    topics = load_topics()
    if safe_name in topics:
        existing_files = topics[safe_name]["files"]
        for sf in saved_files:
            if sf not in existing_files:
                existing_files.append(sf)
    else:
        topics[safe_name] = {
            "display_name": topic_name.strip(),
            "files": saved_files,
        }
    save_topics(topics)

    return {"message": "Files uploaded successfully", "topic": safe_name, "files": saved_files}


@app.get("/api/topics")
def list_topics():
    topics = load_topics()
    result = []
    for key, val in topics.items():
        result.append({
            "id": key,
            "name": val["display_name"],
            "file_count": len(val["files"]),
            "files": val["files"],
        })
    return {"topics": result}


@app.post("/api/generate-custom-questions")
def generate_custom_questions(topic_name: str = Form(...)):
    topics = load_topics()
    safe_name = topic_name.strip()
    if safe_name not in topics:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic = topics[safe_name]
    topic_dir = os.path.join(UPLOAD_DIR, safe_name)

    combined_content = ""
    for filename in topic["files"]:
        file_path = os.path.join(topic_dir, filename)
        if os.path.exists(file_path):
            combined_content += f"\n--- Content from {filename} ---\n"
            combined_content += read_file_content(file_path)

    if not combined_content.strip():
        raise HTTPException(status_code=400, detail="No readable content found in uploaded files")

    combined_content = combined_content[:8000]

    prompt = f"""Based on the following study material, generate exactly 10 unique questions for a student test.

STUDY MATERIAL:
{combined_content}

IMPORTANT: Generate completely NEW and DIFFERENT questions each time. Mix question types: fill-in-the-blank, multiple choice comprehension, vocabulary, grammar, and true/false style (as MCQ).

Return ONLY a JSON array with exactly 10 objects. Each object must have:
- "id": number (1-10)
- "question": the question text
- "options": array of exactly 4 answer choices labeled A, B, C, D
- "correct_answer": the correct option letter (A, B, C, or D)

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


@app.post("/api/submit-custom-answers")
def submit_custom_answers(req: CustomSubmitRequest):
    questions_text = json.dumps(req.questions, indent=2)
    answers_text = json.dumps(req.answers, indent=2)

    prompt = f"""You are grading a custom test for topic "{req.topic_name}".

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
