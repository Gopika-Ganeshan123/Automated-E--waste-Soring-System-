import cv2
import numpy as np
from tensorflow.keras.models import load_model

IMG_SIZE = 224
model = load_model("ewaste_classifier.h5")

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))
    img_blurred = cv2.GaussianBlur(img_resized, (5,5), 0)
    img_normalized = img_blurred / 255.0
    img_final = np.expand_dims(img_normalized, axis=0)
    return img_final

def predict_ewaste(image_path):
    img = preprocess_image(image_path)
    pred = model.predict(img)[0][0]

    label = "NON E-WASTE" if pred > 0.5 else "E-WASTE"
    confidence = float(pred if pred > 0.5 else 1 - pred)

    return label, confidence
