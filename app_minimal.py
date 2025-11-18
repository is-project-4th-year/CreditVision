import http.server
import socketserver
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import os

PORT = 5000

# Simple in-memory database (for demo - would use SQLite in production)
users_db = {}
predictions_db = []

class SimpleAuthAPI(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'status': 'healthy', 'mode': 'minimal'}
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == '/api/admin/users':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            users_list = [{'id': uid, **data} for uid, data in users_db.items()]
            self.wfile.write(json.dumps({'users': users_list}).encode())
            
        else:
            super().do_GET()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/api/auth/register':
            self.handle_register(data)
        elif self.path == '/api/auth/login':
            self.handle_login(data)
        elif self.path == '/api/predict':
            self.handle_predict(data)
        elif self.path == '/api/auth/verify-sms':
            self.handle_verify_sms(data)
        elif self.path == '/api/auth/set-password':
            self.handle_set_password(data)
        else:
            self.send_error(404)
    
    def handle_register(self, data):
        try:
            # Basic validation
            required_fields = ['full_name', 'email', 'phone_number', 'verification_method']
            for field in required_fields:
                if field not in data:
                    self.send_error_response(f'Missing field: {field}')
                    return
            
            # Check if user already exists
            for user_id, user_data in users_db.items():
                if user_data['email'] == data['email']:
                    self.send_error_response('Email already registered')
                    return
                if user_data['phone_number'] == data['phone_number']:
                    self.send_error_response('Phone number already registered')
                    return
            
            # Create new user
            user_id = secrets.token_hex(8)
            verification_code = ''.join(secrets.choice('0123456789') for i in range(6))
            
            users_db[user_id] = {
                'full_name': data['full_name'],
                'email': data['email'],
                'phone_number': data['phone_number'],
                'verification_method': data['verification_method'],
                'verification_code': verification_code,
                'verified': False,
                'password_hash': None,
                'created_at': datetime.now().isoformat()
            }
            
            # In a real app, you'd send email/SMS here
            print(f"🔐 New user registered: {data['email']}")
            print(f"📧 Verification code: {verification_code}")
            
            response = {
                'message': 'Registration successful. Please check your email/SMS for verification code.',
                'user_id': user_id,
                'verification_code': verification_code,  # Only for demo!
                'requires_code_input': data['verification_method'] == 'sms'
            }
            
            self.send_success_response(response)
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def handle_verify_sms(self, data):
        try:
            user_id = data.get('user_id')
            code = data.get('code')
            
            if user_id not in users_db:
                self.send_error_response('User not found')
                return
            
            user = users_db[user_id]
            if user['verification_code'] == code:
                user['verified'] = True
                response = {'message': 'Phone verified successfully'}
                self.send_success_response(response)
            else:
                self.send_error_response('Invalid verification code')
                
        except Exception as e:
            self.send_error_response(str(e))
    
    def handle_set_password(self, data):
        try:
            user_id = data.get('user_id')
            password = data.get('password')
            
            if user_id not in users_db:
                self.send_error_response('User not found')
                return
            
            # Simple password validation
            if len(password) < 8:
                self.send_error_response('Password must be at least 8 characters')
                return
            
            # Hash password (simple demo hashing)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            users_db[user_id]['password_hash'] = password_hash
            
            response = {'message': 'Password set successfully'}
            self.send_success_response(response)
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def handle_login(self, data):
        try:
            email = data.get('email')
            password = data.get('password')
            
            # Find user by email
            user_id = None
            user_data = None
            for uid, data in users_db.items():
                if data['email'] == email:
                    user_id = uid
                    user_data = data
                    break
            
            if not user_id or not user_data:
                self.send_error_response('User not found')
                return
            
            # Check password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user_data['password_hash'] != password_hash:
                self.send_error_response('Invalid password')
                return
            
            if not user_data['verified']:
                self.send_error_response('Please verify your account first')
                return
            
            # Create simple token (in real app, use JWT)
            token = secrets.token_hex(16)
            user_data['token'] = token
            
            response = {
                'message': 'Login successful',
                'access_token': token,
                'user': {
                    'id': user_id,
                    'full_name': user_data['full_name'],
                    'email': user_data['email']
                }
            }
            
            self.send_success_response(response)
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def handle_predict(self, data):
        try:
            # Simple risk prediction based on management score
            management_score = data.get('managingday2day_score', 50)
            
            # Mock risk calculation
            base_risk = 0.3
            risk_adjustment = (100 - management_score) * 0.005
            risk_score = min(base_risk + risk_adjustment, 0.95)
            
            # Determine risk level
            if risk_score < 0.3:
                risk_level = 'Low'
            elif risk_score < 0.6:
                risk_level = 'Medium'
            elif risk_score < 0.8:
                risk_level = 'High'
            else:
                risk_level = 'Critical'
            
            # Save prediction
            prediction_id = len(predictions_db) + 1
            predictions_db.append({
                'id': prediction_id,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'timestamp': datetime.now().isoformat()
            })
            
            response = {
                'riskScore': round(risk_score, 4),
                'riskLevel': risk_level,
                'confidence': round(risk_score * 100, 2),
                'predictionId': prediction_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_success_response(response)
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error_response(self, message):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

print(f"🚀 Starting Minimal Financial Risk API on port {PORT}")
print("🔐 Authentication: Enabled (in-memory)")
print("📊 Predictions: Mock system")
print(f"🔗 Access at: http://localhost:{PORT}")

with socketserver.TCPServer(("", PORT), SimpleAuthAPI) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
