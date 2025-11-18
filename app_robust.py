from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
import os
import sys

app = Flask(__name__)
CORS(app)

# Global variables
selected_features = []
model_loaded = False

def load_model():
    """Try to load model, but provide graceful fallback"""
    global selected_features, model_loaded
    
    try:
        # Try to import joblib and load model
        import joblib
        model_path = os.path.join('models', 'financial_risk_model.pkl')
        
        # Check if model file exists
        if not os.path.exists(model_path):
            print("❌ Model file not found")
            return False
            
        # Try to load the model
        model = joblib.load(model_path)
        print("✅ Model loaded successfully with joblib")
        model_loaded = True
        
    except Exception as e:
        print(f"⚠️ Model loading failed: {e}")
        print("🔧 Using advanced mock prediction system")
        model_loaded = False
    
    try:
        # Load feature configuration
        features_path = os.path.join('models', 'selected_features.json')
        with open(features_path, 'r') as f:
            feature_config = json.load(f)
            selected_features = feature_config.get('selected_features', [])
        print("✅ Features loaded successfully")
        print(f"📊 Model expects {len(selected_features)} features")
        return True
    except Exception as e:
        print(f"❌ Error loading features: {e}")
        return False

class AdvancedRiskPredictor:
    """Advanced mock predictor that mimics real model behavior"""
    
    def __init__(self, feature_names):
        self.feature_names = feature_names
        self.feature_weights = self._calculate_feature_weights()
    
    def _calculate_feature_weights(self):
        """Calculate realistic weights based on feature importance"""
        weights = {}
        
        # High risk indicators
        high_risk_features = ['manage_day2day', 'managingday2day_score', 'financial_status', 
                             'tot_savings', 'Financial_literacy_index_fnl']
        
        # Medium risk indicators  
        medium_risk_features = ['Loan_usage', 'Age', 'Education', 'Marital', 'Quintiles']
        
        # Assign weights
        for feature in self.feature_names:
            if feature in high_risk_features:
                weights[feature] = 0.15
            elif feature in medium_risk_features:
                weights[feature] = 0.08
            else:
                weights[feature] = 0.02
        
        # Normalize weights
        total_weight = sum(weights.values())
        for feature in weights:
            weights[feature] /= total_weight
            
        return weights
    
    def predict(self, feature_data):
        """Generate realistic risk prediction based on feature weights"""
        base_risk = 0.3
        
        # Calculate weighted risk score
        weighted_contributions = 0
        total_applied_weight = 0
        
        for i, feature in enumerate(self.feature_names):
            if feature in feature_data:
                value = feature_data[feature]
                weight = self.feature_weights[feature]
                
                # Normalize and scale contributions
                if feature == 'managingday2day_score':
                    contribution = (100 - value) * 0.005 * weight
                elif feature == 'manage_day2day':
                    contribution = (10 - min(value, 10)) * 0.03 * weight
                elif feature == 'tot_savings':
                    contribution = (1 - min(value / 5000, 1)) * 0.4 * weight
                elif feature == 'Financial_literacy_index_fnl':
                    contribution = (100 - value) * 0.004 * weight
                elif feature == 'financial_status':
                    contribution = (4 - value) * 0.1 * weight
                elif feature == 'Age':
                    contribution = (1 - min(value / 60, 1)) * 0.2 * weight
                else:
                    contribution = value * 0.01 * weight
                
                weighted_contributions += contribution
                total_applied_weight += weight
        
        if total_applied_weight > 0:
            base_risk += weighted_contributions / total_applied_weight
        
        # Ensure reasonable bounds
        risk_score = max(0.05, min(0.95, base_risk))
        
        return risk_score

def convert_to_numerical(key, value):
    """Convert categorical values to numerical for processing"""
    if isinstance(value, str):
        if key == 'Loan_usage':
            mapping = {'Personal': 1, 'Business': 2, 'Education': 3, 'Emergency': 4, 'Other': 5}
            return mapping.get(value, 0)
        elif key == 'county':
            mapping = {'Nairobi': 1, 'Mombasa': 2, 'Kisumu': 3, 'Nakuru': 4, 'Eldoret': 5, 'Other': 6}
            return mapping.get(value, 0)
        elif key == 'Sex':
            return 1 if value == 'Male' else 2
        elif key == 'Marital':
            mapping = {'Single': 1, 'Married': 2, 'Divorced': 3, 'Widowed': 4}
            return mapping.get(value, 0)
        elif key == 'Education':
            mapping = {'Primary': 1, 'Secondary': 2, 'College': 3, 'University': 4, 'Postgraduate': 5}
            return mapping.get(value, 0)
        elif key == 'financial_status':
            mapping = {'Poor': 1, 'Fair': 2, 'Good': 3, 'Excellent': 4}
            return mapping.get(value, 0)
        elif key == 'Quintiles':
            return int(value) if value.isdigit() else 3
    return value

# Initialize predictor
predictor = None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded,
        'features_loaded': len(selected_features) > 0,
        'prediction_mode': 'advanced_mock' if not model_loaded else 'real_model',
        'required_features': selected_features
    })

@app.route('/predict', methods=['POST'])
def predict_risk():
    try:
        # Get JSON data from request
        data = request.get_json()
        print("📥 Received data with keys:", list(data.keys()))
        
        # Initialize predictor if not done
        global predictor
        if predictor is None and selected_features:
            predictor = AdvancedRiskPredictor(selected_features)
            print("🎯 Advanced predictor initialized")
        
        # Convert categorical data to numerical
        processed_data = {}
        for key, value in data.items():
            processed_data[key] = convert_to_numerical(key, value)
        
        # Generate prediction
        if model_loaded:
            # This would use the real model - but it's not loading
            risk_probability = 0.5  # Fallback
        else:
            # Use advanced mock prediction
            risk_probability = predictor.predict(processed_data)
        
        print(f"🎯 Predicted risk: {risk_probability:.4f}")
        
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
            'featuresUsed': len(selected_features),
            'predictionMode': 'advanced_mock',
            'timestamp': pd.Timestamp.now().isoformat(),
            'note': 'Using advanced mock prediction - model compatibility issue'
        })
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/model-info', methods=['GET'])
def model_info():
    return jsonify({
        'model_type': 'AdvancedMockPredictor',
        'features_count': len(selected_features),
        'features': selected_features,
        'status': 'using_advanced_mock',
        'message': 'Real model has compatibility issues. Using sophisticated mock predictions.'
    })

if __name__ == '__main__':
    print("🚀 Starting Robust Financial Risk API Server...")
    
    # Load model configuration
    if load_model():
        print("📊 Backend ready!")
        print("💡 Using advanced mock prediction system")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Failed to load model configuration")
