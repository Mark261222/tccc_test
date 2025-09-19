from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

# Хранилище: { "ПІБ": час_початку }
sessions = {}
TEST_DURATION = 10 * 60  # 10 хв у секундах

@app.route("/")
def index():
    return app.send_static_file("index.html")  # index.html лежить у static/

@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json()
    full_name = data.get("full_name")
    sessions[full_name] = time.time()
    return jsonify({"status":"ok"})

@app.route("/api/time_left")
def time_left():
    full_name = request.args.get("full_name")
    start_time = sessions.get(full_name)
    if not start_time:
        return jsonify({"time_left":0})
    elapsed = time.time() - start_time
    remaining = max(TEST_DURATION - int(elapsed), 0)
    return jsonify({"time_left": remaining})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
