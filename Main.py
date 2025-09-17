from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
import json
import os
import random
import requests
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

from questions import QUESTIONS

app = FastAPI()
templates = Jinja2Templates(directory="templates")

SESSIONS_FILE = "sessions.json"
TIME_LIMIT_MINUTES = 10


# Завантажуємо збережені сесії
if os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
        sessions = json.load(f)
else:
    sessions = {"completed_sessions": {}}

# Перемішуємо відповіді та зберігаємо індекс правильного
for q in QUESTIONS:
    combined = list(zip(q["answers"], range(len(q["answers"]))))
    random.shuffle(combined)
    q["answers"], q["correct_index_orig"] = zip(*combined)
    q["correct"] = q["correct_index_orig"].index(q["correct"])

# Сесії користувачів
user_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/start")
async def start_test(request: Request, full_name: str = Form(...)):
    if len(full_name) < 3 or not full_name.replace(" ", "").isalpha():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "ПІБ має містити мінімум 3 літери та тільки букви"
        })

    if full_name in sessions["completed_sessions"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Ви вже пройшли тест!"
        })

    session_id = str(uuid4())
    user_sessions[session_id] = {
        "name": full_name,
        "answers": [None] * len(QUESTIONS),
        "current": 0,
        "time_left": TIME_LIMIT_MINUTES * 60
    }
    return RedirectResponse(f"/test/{session_id}", status_code=302)

@app.get("/test/{session_id}")
async def get_test(request: Request, session_id: str):
    session = user_sessions.get(session_id)
    if not session:
        return RedirectResponse("/")

    q_index = session["current"]
    question = QUESTIONS[q_index]

    return templates.TemplateResponse("test.html", {
        "request": request,
        "question": question,
        "question_index": q_index,
        "total_questions": len(QUESTIONS),
        "session_id": session_id,
        "answer_selected": session["answers"][q_index],
        "name": session["name"],
        "answers": session["answers"],
        "time_left": session["time_left"],
        "time_limit": TIME_LIMIT_MINUTES
    })

@app.post("/answer/{session_id}")
async def submit_answer(
    session_id: str,
    answer_index: Optional[str] = Form(None),  # приймаємо як рядок
    direction: str = Form(...),
    jump_index: Optional[int] = Form(None),
    time_left: Optional[int] = Form(None)
):
    session = user_sessions.get(session_id)
    if not session:
        return RedirectResponse("/")

    # Конвертуємо у int тільки якщо не порожній
    if answer_index is not None and answer_index != "":
        session["answers"][session["current"]] = int(answer_index)

    # Оновлюємо залишок часу
    if time_left is not None:
        session["time_left"] = time_left

    # Навігація
    if direction == "next" and session["current"] < len(QUESTIONS) - 1:
        session["current"] += 1
    elif direction == "prev" and session["current"] > 0:
        session["current"] -= 1
    elif direction == "jump" and jump_index is not None:
        session["current"] = jump_index
    elif direction == "finish":
        return RedirectResponse(f"/result/{session_id}", status_code=302)

    return RedirectResponse(f"/test/{session_id}", status_code=302)


@app.get("/result/{session_id}")
async def get_result(request: Request, session_id: str):
    session = user_sessions.get(session_id)
    if not session:
        return RedirectResponse("/")

    score = 0
    for i, answer in enumerate(session["answers"]):
        if answer is not None and answer == QUESTIONS[i]["correct"]:
            score += 5

    # Зберігаємо результати та блокуємо повторну здачу
    sessions["completed_sessions"][session["name"]] = {
        "session_id": session_id,
        "score": score
    }
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)

    # Відправка в Telegram
    try:
        text = f"Користувач {session['name']} отримав {score} балів з {len(QUESTIONS)*5}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Помилка при відправці Telegram:", e)

    # Видаляємо сесію
    if session_id in user_sessions:
        del user_sessions[session_id]

    return templates.TemplateResponse("result.html", {
        "request": request,
        "score": score,
        "total": len(QUESTIONS)*5,
        "name": session["name"]
    })
