from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import init_auth, register_auth_routes
from models import db, User, PredictionHistory
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Initialize authentication
init_auth(app)
register_auth_routes(app)

# Global variables for ML model
selected_features = []
model_loaded = False

# ... [Include all your existing ML model loading and prediction code here] ...

@app.route('/api/predict', methods=['POST'])
@jwt_required()
def predict_risk():
    try:
        user_id = get_jwt_identity()
        
        # Get JSON data from request
        data = request.get_json()
        print("📥 Received prediction request from user:", user_id)
        
        # Your existing prediction logic here...
        # [Include the prediction code from app_robust.py]
        
        risk_probability = 0.5  # Placeholder - use your actual prediction logic
        
        # Determine risk level
        if risk_probability < 0.3:
            risk_level = 'Low'
        elif risk_probability < 0.6:
            risk_level = 'Medium' 
        elif risk_probability < 0.8:
            risk_level = 'High'
        else:
            risk_level = 'Critical'
        
        # Save prediction to history
        prediction = PredictionHistory(
            user_id=user_id,
            risk_score=risk_probability,
            risk_level=risk_level,
            input_data=json.dumps(data)
        )
        db.session.add(prediction)
        db.session.commit()
        
        return jsonify({
            'riskScore': round(risk_probability, 4),
            'riskLevel': risk_level,
            'confidence': round(risk_probability * 100, 2),
            'predictionId': prediction.id,
            'timestamp': pd.Timestamp.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/history', methods=['GET'])
@jwt_required()
def get_prediction_history():
    user_id = get_jwt_identity()
    
    predictions = PredictionHistory.query.filter_by(user_id=user_id).order_by(
        PredictionHistory.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'predictions': [
            {
                'id': p.id,
                'riskScore': p.risk_score,
                'riskLevel': p.risk_level,
                'createdAt': p.created_at.isoformat()
            } for p in predictions
        ]
    })

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("🚀 Starting Financial Risk API with Authentication...")
    app.run(host='0.0.0.0', port=5000, debug=True)
