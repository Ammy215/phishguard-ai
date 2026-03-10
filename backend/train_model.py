print("=== TRAINING STARTED ===")
# backend/train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from urllib.parse import urlparse

# Load dataset
df = pd.read_csv("PhiUSIIL_Phishing_URL_Dataset.csv")

# Select only URL-based features we can reproduce
df = df[
    [
        "URL",
        "URLLength",
        "DomainLength",
        "IsDomainIP",
        "TLDLength",
        "NoOfSubDomain",
        "IsHTTPS",
        "label",
    ]
]

# Features & target
X = df.drop(columns=["URL", "label"])
y = df["label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train model
model = RandomForestClassifier(
    n_estimators=50,     # fewer trees → much faster
    max_depth=10,        # limit tree size
    n_jobs=-1,           # use all CPU cores
    random_state=42
)
print("=== FITTING MODEL ===")
model.fit(X_train, y_train)
print("=== MODEL FIT COMPLETE ===")


# Evaluate
preds = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, preds))

# Save model
joblib.dump(model, "phish_model.joblib")
print("Saved model as phish_model.joblib")
