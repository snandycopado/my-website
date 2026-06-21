from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# This allows your React app to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll restrict this later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from Python!"}

@app.get("/data")
def get_data():
    return {
        "items": ["Apple", "Banana", "Cherry"],
        "count": 3
    }