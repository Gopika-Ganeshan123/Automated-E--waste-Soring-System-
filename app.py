from flask import Flask, render_template, request, jsonify
import os
import csv
from datetime import datetime
from model import predict_ewaste
from firebase_config import db, rtdb_ref

app = Flask(__name__)

UPLOAD_FOLDER = "static/captures"
LOG_FILE = "logs/classification_logs.csv"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Home
@app.route("/")
def index():
    return render_template("index.html")

# Detection Page
@app.route("/detect")
def detect():
    return render_template("detect.html")

# Logs Page
@app.route("/logs")
def logs():
    try:
        bins = rtdb_ref.child("bins").get() or {}

        def bin_status(distance):
            if distance is not None and distance < 5:
                return "FULL"
            return "NORMAL"

        bin_data = {
            "bin1": bin_status(bins.get("bin1_distance")),
            "bin2": bin_status(bins.get("bin2_distance")),
            "bin3": bin_status(bins.get("bin3_distance")),
        }

    except Exception as e:
        print("Firebase error:", e)
        bin_data = {"bin1": "UNKNOWN", "bin2": "UNKNOWN", "bin3": "UNKNOWN"}

    return render_template("logs.html", bins=bin_data)



@app.route("/predict", methods=["POST"])
def predict():
    image = request.files["image"]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(path)

    label, confidence = predict_ewaste(path)

    # Save log locally
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([filename, label, confidence, datetime.now()])

    # Firestore logs (always save)
    db.collection("ewaste_logs").add({
        "image": filename,
        "label": label,
        "confidence": confidence,
        "timestamp": datetime.now()
    })

    # ---------- CONFIDENCE LOGIC ----------
    if confidence < 0.70:
        # Low confidence → block hardware
        rtdb_ref.child("latest").set({
            "label": "NO_WASTE",
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "consumed": True   # ESP32 will IGNORE
        })

        return jsonify({
            "status": "low_confidence",
            "confidence": confidence
        })

    # ---------- NORMAL FLOW (>=70%) ----------
    rtdb_ref.child("latest").set({
        "label": label,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat(),
        "consumed": False
    })

    return jsonify({
        "status": "ok",
        "label": label,
        "confidence": confidence,
        "image": path
    })

if __name__ == "__main__":
    app.run(debug=True)
