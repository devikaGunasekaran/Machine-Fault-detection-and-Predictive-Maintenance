import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report
from imblearn.combine import SMOTEENN
from xgboost import XGBClassifier
import joblib

# Load and clean dataset
df = pd.read_csv('industrial_fault_detection_data_1000.csv')
df.columns = ['Timestamp', 'Vibration', 'Temperature', 'Pressure', 'RMS_Vibration', 'Mean_Temp', 'Fault_Label']
df = df.drop(columns=['Timestamp'])

X = df.drop(columns=['Fault_Label'])
y = df['Fault_Label']

# Apply SMOTEENN
sm = SMOTEENN()
X_resampled, y_resampled = sm.fit_resample(X, y)

# Scale features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X_resampled)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_resampled, test_size=0.3, random_state=42)

# Train model
model = XGBClassifier(eval_metric='mlogloss', use_label_encoder=False)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model and scaler
joblib.dump(model, 'xgb_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
