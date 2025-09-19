from flask import Flask, request, jsonify, send_from_directory
import time

app = Flask(__name__, static_folder="static")

# Зберігаємо час старту тесту для кожного користувача
sessions = {}
TEST_DURATION = 10 * 60  # 10 хвилин у секундах

# Маршрут для index.html
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# Старт тесту
@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json()
    full_name = data.get("full_name")
    if not full_name:
        return jsonify({"error":"Потрібне ПІБ"}), 400

    sessions[full_name] = time.time()
    return jsonify({"status":"ok"})

# Залишок часу
@app.route("/api/time_left")
def time_left():
    full_name = request.args.get("full_name")
    start_time = sessions.get(full_name)
    if not start_time:
        return jsonify({"time_left":0})
    elapsed = time.time() - start_time
    remaining = max(TEST_DURATION - int(elapsed), 0)
    return jsonify({"time_left": remaining})

# Повернення запитань (приклад статичних)
@app.route("/api/questions")
def questions():
    # Тут можна повертати JSON з усіма 20 питаннями або HTML
    html = """
    <h2>Питання тесту</h2>
    <ol>
        <li>Питання 1: ...</li>
        <li>Питання 2: ...</li>
        <li>Питання 3: ...</li>
        <li>...</li>
        <li>Питання 20: ...</li>
    </ol>
    """
    return jsonify({"html": html})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
