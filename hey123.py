import kagglehub, pathlib

dataset_id = "drkhaledmohsin/national-heart-foundation-2023-ecg-dataset"
dataset_path = kagglehub.dataset_download(dataset_id)
print("Downloaded to:", dataset_path)

# Point to the folder that actually contains class subfolders
data_dir = pathlib.Path(dataset_path) / "ECG Data"
assert data_dir.exists(), f"Could not find 'ECG Data' in {dataset_path}"
print("Using data_dir:", data_dir)

# Quick sanity check of classes
classes = sorted([p.name for p in data_dir.iterdir() if p.is_dir()])
print("Classes:", classes)
assert len(classes) >= 2, "Need at least two class folders inside 'ECG Data'."

import tensorflow as tf

from tensorflow.keras.utils import image_dataset_from_directory

IMG_SIZE = (128, 128)    # Safe, standard size
BATCH = 32
VAL_SPLIT = 0.2

train_ds = image_dataset_from_directory(
    data_dir,
    validation_split=VAL_SPLIT,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH
)
val_ds = image_dataset_from_directory(
    data_dir,
    validation_split=VAL_SPLIT,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH
)

# Access class names before caching and prefetching
NUM_CLASSES = len(train_ds.class_names)
class_names = train_ds.class_names

# Basic augmentation (on-the-fly, only for training)
data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.02),
    tf.keras.layers.RandomZoom(0.1),
])

def aug(x, y): return data_augmentation(x), y
train_ds = train_ds.map(aug, num_parallel_calls=tf.data.AUTOTUNE)

# Cache + prefetch for speed
train_ds = train_ds.cache().prefetch(tf.data.AUTOTUNE)
val_ds   = val_ds.cache().prefetch(tf.data.AUTOTUNE)

class_names

from tensorflow.keras import layers, models

model = models.Sequential([
    layers.Input(shape=(*IMG_SIZE, 3)),
    layers.Rescaling(1./255),

    layers.Conv2D(32, 3, activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(128, 3, activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(128, 3, activation="relu"),
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.4),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(len(classes), activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

ckpt_path = "/content/ecg_cnn_best.keras"
callbacks = [
    EarlyStopping(monitor="val_accuracy", patience=5, restore_best_weights=True),
    ModelCheckpoint(ckpt_path, monitor="val_accuracy", save_best_only=True)
]

EPOCHS = 20
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

print("Best model saved to:", ckpt_path)

import matplotlib.pyplot as plt

plt.figure()
plt.plot(history.history["accuracy"], label="train acc")
plt.plot(history.history["val_accuracy"], label="val acc")
plt.xlabel("Epoch"); plt.ylabel("Accuracy"); plt.legend(); plt.title("Training vs Validation Accuracy")
plt.show()

plt.figure()
plt.plot(history.history["loss"], label="train loss")
plt.plot(history.history["val_loss"], label="val loss")
plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.legend(); plt.title("Training vs Validation Loss")
plt.show()

import tensorflow as tf
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from google.colab import files


# Load the model with the best weights from the training history
model = history.model


class_names = ["Abnormal Heartbeat Patients",
               "Myocardial Infarction Patients",
               "Normal Person",
               "Patient that have History of Myocardial Infraction"]


try:
    # Attempt to load an image from a URL
    url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/ecg.csv" # Example direct link - THIS IS NOT A VALID IMAGE LINK. Replace with a real image URL if available.
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    print("Image loaded from URL ✅")
except:
    print("URL failed or is not an image, please upload an image instead.")
    # If URL fails, prompt user to upload
    uploaded = files.upload()
    img_path = list(uploaded.keys())[0]
    img = Image.open(img_path).convert("RGB")
    print("Image loaded from upload ✅")


IMG_SIZE = (128, 128) # Use the same size the model was trained on
img = img.resize(IMG_SIZE)
x = tf.keras.utils.img_to_array(img)
x = np.expand_dims(x, axis=0) / 255.0


probs = model.predict(x, verbose=0)
pred_idx = int(np.argmax(probs))

print("Predicted:", class_names[pred_idx])
print("Confidence:", float(probs[0][pred_idx]))
