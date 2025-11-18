from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import json
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for model and features
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
        print(f"📊 Model expects {len(selected_features)} features: {selected_features}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'features_loaded': len(selected_features) > 0
    })

@app.route('/predict', methods=['POST'])
def predict_risk():
    """Predict financial risk based on input features"""
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        # Get JSON data from request
        data = request.get_json()
        
        # Extract features (this will need to match your model's expected features)
        input_features = {}
        
        # Map frontend fields to model features (you'll need to adjust this)
        feature_mapping = {
            'loanUsage': 'Loan_usage',
            'country': 'country', 
            'daysActive': 'number_day/day',
            'fundedLoans': 'number_fund_loan',
            'managementScore': 'managingday/day_score',
            'dailyActivity': 'manager_day/day'
        }
        
        # Create feature vector
        feature_vector = []
        for feature in selected_features:
            # Try to map from frontend input
            frontend_field = None
            for frontend_key, model_feature in feature_mapping.items():
                if model_feature == feature:
                    frontend_field = frontend_key
                    break
            
            if frontend_field and frontend_field in data:
                feature_vector.append(data[frontend_field])
            else:
                # If feature not provided, use default (you might want to handle this differently)
                feature_vector.append(0)
        
        # Convert to numpy array and reshape for prediction
        features_array = np.array(feature_vector).reshape(1, -1)
        
        # Make prediction
        risk_probability = model.predict_proba(features_array)[0][1]  # Probability of class 1 (risky)
        
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
            'featuresUsed': selected_features,
            'timestamp': pd.Timestamp.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'model_type': str(type(model)),
        'features_count': len(selected_features),
        'features': selected_features,
        'model_params': model.get_params() if hasattr(model, 'get_params') else 'Not available'
    })

if __name__ == '__main__':
    print("🚀 Starting Financial Risk API Server...")
    
    # Load model on startup
    if load_model():
        print("📊 Model loaded successfully!")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Failed to load model. Please check your model files.")
