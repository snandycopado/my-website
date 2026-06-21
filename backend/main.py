import os
import json
import base64
import anthropic
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")
TOPICS_FILE = os.path.join(DATA_DIR, "topics.json")
os.makedirs(DATA_DIR, exist_ok=True)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

_topics_cache = None


def load_topics():
    global _topics_cache
    if _topics_cache is not None:
        return _topics_cache
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                _topics_cache = json.load(f)
                return _topics_cache
        except Exception:
            pass
    _topics_cache = {}
    return _topics_cache


def save_topics(topics):
    global _topics_cache
    _topics_cache = topics
    try:
        with open(TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2)
    except Exception:
        pass


def is_image(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS


def extract_text_from_image_bytes(file_bytes, filename):
    ext = os.path.splitext(filename)[1].lower()
    media_type = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    }.get(ext, "image/png")

    image_data = base64.standard_b64encode(file_bytes).decode("utf-8")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_data},
                },
                {
                    "type": "text",
                    "text": "Extract ALL the text content from this image. If it contains questions, paragraphs, vocabulary, grammar rules, stories, or any educational content, extract it completely and accurately. Return only the extracted text, nothing else.",
                },
            ],
        }],
    )
    return response.content[0].text


def extract_text_from_pdf_bytes(file_bytes):
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


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

    topics = load_topics()
    if safe_name not in topics:
        topics[safe_name] = {
            "display_name": topic_name.strip(),
            "files": [],
        }

    for file in files:
        file_bytes = await file.read()
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()

        # Extract text content
        if ext in IMAGE_EXTENSIONS:
            extracted_text = extract_text_from_image_bytes(file_bytes, filename)
            file_data_url = f"data:image/{ext.lstrip('.')};base64,{base64.standard_b64encode(file_bytes).decode('utf-8')}"
        elif ext == ".pdf":
            extracted_text = extract_text_from_pdf_bytes(file_bytes)
            file_data_url = f"data:application/pdf;base64,{base64.standard_b64encode(file_bytes).decode('utf-8')}"
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
            file_data_url = None

        file_entry = {
            "filename": filename,
            "type": "image" if ext in IMAGE_EXTENSIONS else ("pdf" if ext == ".pdf" else "text"),
            "extracted_text": extracted_text[:10000],
            "data_url": file_data_url,
        }

        existing_filenames = [f["filename"] for f in topics[safe_name]["files"]]
        if filename in existing_filenames:
            idx = existing_filenames.index(filename)
            topics[safe_name]["files"][idx] = file_entry
        else:
            topics[safe_name]["files"].append(file_entry)

    save_topics(topics)

    return {
        "message": "Files uploaded successfully",
        "topic": safe_name,
        "files": [f["filename"] for f in topics[safe_name]["files"]],
    }


@app.get("/api/topics")
def list_topics():
    topics = load_topics()
    result = []
    for key, val in topics.items():
        result.append({
            "id": key,
            "name": val["display_name"],
            "file_count": len(val["files"]),
            "files": [f["filename"] for f in val["files"]],
        })
    return {"topics": result}


@app.get("/api/topics/{topic_id}/files/{filename}/view")
def view_file(topic_id: str, filename: str):
    topics = load_topics()
    if topic_id not in topics:
        raise HTTPException(status_code=404, detail="Topic not found")

    for f in topics[topic_id]["files"]:
        if f["filename"] == filename:
            return {
                "filename": f["filename"],
                "type": f["type"],
                "extracted_text": f["extracted_text"],
                "data_url": f.get("data_url"),
            }

    raise HTTPException(status_code=404, detail="File not found")


@app.post("/api/generate-custom-questions")
def generate_custom_questions(topic_name: str = Form(...)):
    topics = load_topics()
    safe_name = topic_name.strip()
    if safe_name not in topics:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic = topics[safe_name]

    combined_content = ""
    for f in topic["files"]:
        combined_content += f"\n--- Content from {f['filename']} ---\n"
        combined_content += f["extracted_text"]

    if not combined_content.strip():
        raise HTTPException(status_code=400, detail="No readable content found in uploaded files")

    combined_content = combined_content[:8000]

    prompt = f"""Based on the following study material, generate exactly 10 unique questions for a student test.

STUDY MATERIAL:
{combined_content}

IMPORTANT: Generate completely NEW and DIFFERENT questions each time. Mix question types: fill-in-the-blank, multiple choice comprehension, vocabulary, grammar, and true/false style (as MCQ). Questions must be based on the content of the study material provided above.

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
