from fastapi import FastAPI
from pydantic import BaseModel
from chat_service import process_message

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Welcome to virtual AI Companion"}

@app.post("/chat")
def chat(request: ChatRequest):
    reply=process_message(request.message)
    return {
        "reply":reply
        
    }