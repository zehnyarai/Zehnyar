from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()

# اتصال به هوش مصنوعی با استفاده از کلیدی که بعداً در Render ست می‌کنیم
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Zehnyar API is Running!"}

@app.post("/chat")
async def chat_with_pishai(request: ChatRequest):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "تو 'ذهن‌یار' (pishai) هستی. یک متخصص منطق و استدلال. وظیفه تو تحلیل مغالطه‌ها و آموزش درست حرف زدن به زبان فارسی است."},
                {"role": "user", "content": request.message}
            ]
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
      
