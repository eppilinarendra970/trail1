from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import json
import os
import threading

DATA_FILE = "students.json"
LOCK = threading.Lock()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)  # you can remove if frontend served from same origin

def load_students():
    if not os.path.exists(DATA_FILE):
        return []
    with LOCK:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
            except Exception:
                return []

def save_students(students):
    with LOCK:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=2, ensure_ascii=False)

def find_student_by_id(students, sid):
    for s in students:
        if s and len(s) > 0 and str(s[0]) == str(sid):
            return s
    return None

@app.route("/api/students", methods=["GET"])
def api_list_students():
    students = load_students()
    return jsonify(students), 200

@app.route("/api/students", methods=["POST"])
def api_create_student():
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400

    # Expect payload to be dict: { "id": "...", "name": "...", "age":"", "course":"", "marks":"" }
    required = ["id", "name"]
    if not all(k in payload and str(payload[k]).strip() for k in required):
        return jsonify({"error": "id and name required"}), 400

    students = load_students()
    if find_student_by_id(students, payload["id"]):
        return jsonify({"error": "Student ID already exists"}), 409

    row = [
        str(payload.get("id")),
        str(payload.get("name")),
        str(payload.get("age", "")),
        str(payload.get("course", "")),
        str(payload.get("marks", ""))
    ]
    students.append(row)
    save_students(students)
    return jsonify(row), 201

@app.route("/api/students/<sid>", methods=["GET"])
def api_get_student(sid):
    students = load_students()
    s = find_student_by_id(students, sid)
    if not s:
        return jsonify({"error": "not found"}), 404
    return jsonify(s), 200

@app.route("/api/students/<sid>", methods=["PUT"])
def api_update_student(sid):
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400

    students = load_students()
    idx = next((i for i,s in enumerate(students) if str(s[0])==str(sid)), None)
    if idx is None:
        return jsonify({"error": "not found"}), 404

    # update allowed fields
    students[idx][1] = str(payload.get("name", students[idx][1]))
    students[idx][2] = str(payload.get("age", students[idx][2]))
    students[idx][3] = str(payload.get("course", students[idx][3]))
    students[idx][4] = str(payload.get("marks", students[idx][4]))
    save_students(students)
    return jsonify(students[idx]), 200

@app.route("/api/students/<sid>", methods=["DELETE"])
def api_delete_student(sid):
    students = load_students()
    idx = next((i for i,s in enumerate(students) if str(s[0])==str(sid)), None)
    if idx is None:
        return jsonify({"error": "not found"}), 404
    removed = students.pop(idx)
    save_students(students)
    return jsonify(removed), 200

# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # If path file exists in static, serve it; otherwise serve index.html
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    # Create empty data file if missing
    if not os.path.exists(DATA_FILE):
        save_students([])
    app.run(host="0.0.0.0", port=5000, debug=True)
