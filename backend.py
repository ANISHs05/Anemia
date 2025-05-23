from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import numpy as np
import tensorflow as tf
from keras import models
from PIL import Image
import io
import os
import gdown

# Google Drive file ID for your .h5 model
file_id = "14SWnczT3aMRRpkdezk7uO0vDOEttT159"
url = f"https://drive.google.com/uc?id={file_id}"
output = "backend/anemia_classification_model.h5"

# Download only if not already present
if not os.path.exists(output):
    print("Downloading anemia_classification_model.h5 from Google Drive...")
    gdown.download(url, output, quiet=False)
else:
    print("Model file already exists. Skipping download.")



# Initialize Flask app
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
CORS(app)  # Enable CORS

# Load pre-trained model
MODEL_PATH = "backend/anemia_classification_model.h5"
model = models.load_model(MODEL_PATH)

# Directory for saving uploaded images
UPLOAD_FOLDER = "backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Image preprocessing function
def preprocess_image(img):
    img = img.resize((224, 224))  # Resize to model input size
    img = np.array(img) / 255.0   # Normalize pixel values
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

# Serve frontend (index.html)
@app.route("/")
def serve_frontend():
    return render_template("index.html")

# API Route for Prediction
@app.route("/api/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Convert file to image
        img = Image.open(io.BytesIO(file.read())).convert("RGB")
        img_array = preprocess_image(img)

        # Save image for future analysis
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        img.save(file_path)

        # Model prediction
        prediction = model.predict(img_array)[0][0]
        result = "Anemic" if prediction > 0.5 else "Healthy"
        confidence = float(prediction) if prediction > 0.5 else float(1 - prediction)

        return jsonify({"prediction": result, "confidence": confidence})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve uploaded images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Run the Flask app
if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)
