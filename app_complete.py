from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import json
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Global variables
model = None
selected_features = []

def load_model():
    """Load the trained model and feature list"""
    global model, selected_features
    
    try:
        # Load model
        model_path = os.path.join('models', 'financial_risk_model.pkl')
        model = joblib.load(model_path)
        print("✅ Model loaded successfully")
        
        # Load feature configuration
        features_path = os.path.join('models', 'selected_features.json')
        with open(features_path, 'r') as f:
            feature_config = json.load(f)
            selected_features = feature_config.get('selected_features', [])
        print("✅ Features loaded successfully")
        print(f"📊 Model expects {len(selected_features)} features")
        
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'features_loaded': len(selected_features) > 0,
        'required_features': selected_features
    })

@app.route('/predict', methods=['POST'])
def predict_risk():
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        # Get JSON data from request
        data = request.get_json()
        print("📥 Received data with keys:", list(data.keys()))
        
        # Create feature vector in exact order expected by model
        feature_vector = []
        missing_features = []
        
        for feature in selected_features:
            if feature in data:
                # Convert categorical features to numerical if needed
                value = data[feature]
                
                # Handle specific categorical conversions
                if feature == 'Loan_usage' and isinstance(value, str):
                    usage_map = {'Personal': 1, 'Business': 2, 'Education': 3, 'Emergency': 4, 'Other': 5}
                    value = usage_map.get(value, 0)
                
                elif feature == 'county' and isinstance(value, str):
                    county_map = {'Nairobi': 1, 'Mombasa': 2, 'Kisumu': 3, 'Nakuru': 4, 'Eldoret': 5, 'Other': 6}
                    value = county_map.get(value, 0)
                
                elif feature == 'Sex' and isinstance(value, str):
                    value = 1 if value == 'Male' else 2
                
                elif feature == 'Marital' and isinstance(value, str):
                    marital_map = {'Single': 1, 'Married': 2, 'Divorced': 3, 'Widowed': 4}
                    value = marital_map.get(value, 0)
                
                elif feature == 'Education' and isinstance(value, str):
                    education_map = {'Primary': 1, 'Secondary': 2, 'College': 3, 'University': 4, 'Postgraduate': 5}
                    value = education_map.get(value, 0)
                
                elif feature == 'financial_status' and isinstance(value, str):
                    status_map = {'Poor': 1, 'Fair': 2, 'Good': 3, 'Excellent': 4}
                    value = status_map.get(value, 0)
                
                feature_vector.append(float(value))
            else:
                missing_features.append(feature)
                # Use safe default for missing features
                feature_vector.append(0.0)
        
        if missing_features:
            print(f"⚠️ Missing features: {missing_features}")
        
        print(f"📊 Feature vector created: {len(feature_vector)} values")
        
        # Convert to numpy array and reshape for prediction
        features_array = np.array(feature_vector).reshape(1, -1)
        
        # Make prediction
        try:
            risk_probability = model.predict_proba(features_array)[0][1]  # Probability of class 1 (risky)
            print(f"🎯 Model prediction: {risk_probability:.4f}")
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            # Fallback to simple heuristic
            management_score = data.get('managingday2day_score', 50)
            risk_probability = 0.3 + (100 - management_score) * 0.005
            risk_probability = min(risk_probability, 0.95)
        
        # Determine risk level
        if risk_probability < 0.3:
            risk_level = 'Low'
        elif risk_probability < 0.6:
            risk_level = 'Medium' 
        elif risk_probability < 0.8:
            risk_level = 'High'
        else:
            risk_level = 'Critical'
        
        return jsonify({
            'riskScore': round(risk_probability, 4),
            'riskLevel': risk_level,
            'confidence': round(risk_probability * 100, 2),
            'featuresUsed': len(feature_vector),
            'missingFeatures': missing_features,
            'timestamp': pd.Timestamp.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Overall error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/model-info', methods=['GET'])
def model_info():
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'model_type': str(type(model)),
        'features_count': len(selected_features),
        'features': selected_features
    })

if __name__ == '__main__':
    print("🚀 Starting Complete Financial Risk API Server...")
    
    # Load model on startup
    if load_model():
        print("📊 Model loaded successfully!")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Failed to load model. Please check your model files.")
