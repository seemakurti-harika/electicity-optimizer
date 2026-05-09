import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Load dataset
data = pd.read_csv('dataset/energy_data.csv')

# Features and target
X = data[['Power', 'Hours']]
y = data['Bill']

# Train model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
model.fit(X, y)

# Save model
joblib.dump(model, 'model.pkl')

print("Model Trained Successfully")
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

score = r2_score(y_test, predictions)

print("Model Accuracy:", score)