from flask import Flask, request, jsonify, url_for, render_template_string
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, bcrypt, User, PredictionHistory
import re
import os
from datetime import timedelta

# Email and SMS configuration (you'll need to set these environment variables)
EMAIL_API_KEY = os.getenv('SENDGRID_API_KEY', 'your_sendgrid_key')
SMS_API_KEY = os.getenv('TWILIO_API_KEY', 'your_twilio_key')

def init_auth(app):
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    
    # JWT config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///financial_risk.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return jwt

# Password validation
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

# Email verification (mock - you'll need to implement real email sending)
def send_verification_email(email, verification_url):
    print(f"📧 Verification email sent to {email}")
    print(f"🔗 Verification URL: {verification_url}")
    # In production, integrate with SendGrid:
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    return True

# SMS verification (mock - you'll need to implement real SMS sending)
def send_verification_sms(phone_number, code):
    print(f"📱 Verification SMS sent to {phone_number}")
    print(f"🔢 Verification code: {code}")
    # In production, integrate with Twilio or Africa's Talking
    return True

# Auth routes
def register_auth_routes(app):
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'phone_number', 'verification_method']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Validate verification method
            if data['verification_method'] not in ['email', 'sms']:
                return jsonify({'error': 'Verification method must be email or sms'}), 400
            
            # Validate email format
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Validate phone number (basic Safaricom format)
            phone_regex = r'^254[17]\d{8}$'  # Kenyan format
            if not re.match(phone_regex, data['phone_number']):
                return jsonify({'error': 'Invalid Safaricom phone number format. Use 254XXXXXXXXX'}), 400
            
            # Check if user already exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already registered'}), 400
            
            if User.query.filter_by(phone_number=data['phone_number']).first():
                return jsonify({'error': 'Phone number already registered'}), 400
            
            # Create new user
            user = User(
                full_name=data['full_name'],
                email=data['email'],
                phone_number=data['phone_number'],
                verification_method=data['verification_method']
            )
            
            # Generate verification code
            verification_code = user.generate_verification_code()
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification
            if data['verification_method'] == 'email':
                verification_url = f"http://localhost:8000/verify-email?user_id={user.id}&code={verification_code}"
                send_verification_email(data['email'], verification_url)
                return jsonify({
                    'message': 'Registration successful. Please check your email for verification link.',
                    'user_id': user.id
                })
            else:  # sms
                send_verification_sms(data['phone_number'], verification_code)
                return jsonify({
                    'message': 'Registration successful. Please check your SMS for verification code.',
                    'user_id': user.id,
                    'requires_code_input': True
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/auth/verify-email', methods=['GET'])
    def verify_email():
        user_id = request.args.get('user_id')
        code = request.args.get('code')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Invalid verification link'}), 400
        
        if user.is_verification_code_valid(code):
            user.email_verified = True
            db.session.commit()
            
            # Return HTML page for password setup
            html_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email Verified - Set Password</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
                    <h2 class="text-2xl font-bold text-green-600 mb-4">✓ Email Verified Successfully!</h2>
                    <p class="text-gray-600 mb-6">Please set your password to complete registration.</p>
                    
                    <form id="passwordForm">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">Password</label>
                            <input type="password" id="password" class="w-full px-3 py-2 border rounded-md" 
                                   placeholder="Enter your password" required>
                            <div id="passwordErrors" class="text-red-500 text-sm mt-1"></div>
                        </div>
                        
                        <div class="mb-6">
                            <label class="block text-gray-700 text-sm font-bold mb-2">Confirm Password</label>
                            <input type="password" id="confirmPassword" class="w-full px-3 py-2 border rounded-md" 
                                   placeholder="Confirm your password" required>
                            <div id="confirmErrors" class="text-red-500 text-sm mt-1"></div>
                        </div>
                        
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                            Set Password & Complete Registration
                        </button>
                    </form>
                </div>
                
                <script>
                    document.getElementById('passwordForm').addEventListener('submit', async (e) => {
                        e.preventDefault();
                        
                        const password = document.getElementById('password').value;
                        const confirmPassword = document.getElementById('confirmPassword').value;
                        
                        // Basic validation
                        if (password !== confirmPassword) {
                            document.getElementById('confirmErrors').textContent = 'Passwords do not match';
                            return;
                        }
                        
                        if (password.length < 8) {
                            document.getElementById('passwordErrors').textContent = 'Password must be at least 8 characters';
                            return;
                        }
                        
                        try {
                            const response = await fetch('/api/auth/set-password', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    user_id: '{{ user_id }}',
                                    password: password
                                })
                            });
                            
                            const result = await response.json();
                            
                            if (response.ok) {
                                alert('Password set successfully! You can now login.');
                                window.location.href = 'http://localhost:8000/login';
                            } else {
                                alert('Error: ' + result.error);
                            }
                        } catch (error) {
                            alert('Network error. Please try again.');
                        }
                    });
                </script>
            </body>
            </html>
            '''
            return render_template_string(html_template.replace('{{ user_id }}', user_id))
        else:
            return jsonify({'error': 'Invalid or expired verification code'}), 400
    
    @app.route('/api/auth/verify-sms', methods=['POST'])
    def verify_sms():
        data = request.get_json()
        user_id = data.get('user_id')
        code = data.get('code')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Invalid user'}), 400
        
        if user.is_verification_code_valid(code):
            user.phone_verified = True
            db.session.commit()
            
            return jsonify({
                'message': 'Phone number verified successfully. Please set your password.',
                'user_id': user.id
            })
        else:
            return jsonify({'error': 'Invalid or expired verification code'}), 400
    
    @app.route('/api/auth/set-password', methods=['POST'])
    def set_password():
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Invalid user'}), 400
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Set password
        user.set_password(password)
        db.session.commit()
        
        return jsonify({'message': 'Password set successfully. You can now login.'})
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.email_verified and not user.phone_verified:
            return jsonify({'error': 'Please verify your account before logging in'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        })
    
    @app.route('/api/auth/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        return jsonify({
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        })
    
    return app
