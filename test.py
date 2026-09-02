import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model

# ==============================
# CONFIG
# ==============================
IMG_SIZE = 224
CAMERA_INDEX = 2       # 0 for default webcam
TIMER_SECONDS = 5

# ==============================
# LOAD MODEL
# ==============================
model = load_model("ewaste_classifier.h5")
print("✅ Model Loaded!")

# ==============================
# PREPROCESS FUNCTION (same logic)
# ==============================
def preprocess_frame(frame):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))

    # Gaussian Blur
    img_blurred = cv2.GaussianBlur(img_resized, (5, 5), 0)

    # Normalize
    img_normalized = img_blurred / 255.0

    # Expand dims → (1, 224, 224, 3)
    img_final = np.expand_dims(img_normalized, axis=0)

    return img_final, img_rgb

# ==============================
# CAMERA CAPTURE WITH TIMER
# ==============================
def capture_image_with_timer():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("❌ Camera not accessible")

    start_time = time.time()
    captured_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        elapsed = int(time.time() - start_time)
        remaining = TIMER_SECONDS - elapsed

        if remaining > 0:
            cv2.putText(
                frame,
                f"Capturing in {remaining} sec...",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
        else:
            captured_frame = frame.copy()
            break

        cv2.imshow("Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()

    if captured_frame is None:
        raise RuntimeError("❌ Image capture failed")

    return captured_frame

# ==============================
# INFERENCE
# ==============================
def run_inference_on_camera_image():
    frame = capture_image_with_timer()
    processed_img, original_img = preprocess_frame(frame)

    pred = model.predict(processed_img)[0][0]

    label = "NON E-WASTE" if pred > 0.5 else "E-WASTE"
    confidence = pred if pred > 0.5 else (1 - pred)

    # Display result
    plt.figure(figsize=(6, 6))
    plt.imshow(original_img)
    plt.title(f"Prediction: {label}\nConfidence: {confidence:.2f}")
    plt.axis("off")
    plt.show()

    print("🔹 Final Prediction:", label)
    print("🔹 Confidence:", confidence)

    return label, confidence

# ==============================
# RUN
# ==============================
run_inference_on_camera_image()
