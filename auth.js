// auth.js

// Global authentication functions
window.showError = function(message) {
    console.error('Error:', message);
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

window.resetButton = function(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
        if (buttonId === 'login-btn') {
            button.textContent = 'Login';
        } else if (buttonId === 'register-btn') {
            button.textContent = 'Create Account';
        } else if (buttonId === 'google-login-btn') {
            button.textContent = 'Sign in with Google';
        }
        button.disabled = false;
    }
}

window.loginWithEmail = function(email, password) {
    console.log('Attempting login with:', email);
    
    if (typeof auth === 'undefined') {
        showError('Authentication not initialized. Please refresh the page.');
        return;
    }
    
    auth.signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            console.log('Login successful!');
            window.location.href = 'http://localhost:8000';
        })
        .catch((error) => {
            console.error('Login error:', error);
            let errorMessage = 'Login failed. ';
            
            switch (error.code) {
                case 'auth/invalid-email':
                    errorMessage += 'Invalid email address.';
                    break;
                case 'auth/user-disabled':
                    errorMessage += 'This account has been disabled.';
                    break;
                case 'auth/user-not-found':
                    errorMessage += 'No account found with this email.';
                    break;
                case 'auth/wrong-password':
                    errorMessage += 'Incorrect password.';
                    break;
                default:
                    errorMessage += error.message;
            }
            
            showError(errorMessage);
            resetButton('login-btn');
        });
}

window.registerWithEmail = function(email, password) {
    console.log('Attempting registration with:', email);
    
    if (typeof auth === 'undefined') {
        showError('Authentication not initialized. Please refresh the page.');
        return;
    }
    
    auth.createUserWithEmailAndPassword(email, password)
        .then((userCredential) => {
            console.log('Registration successful!');
            window.location.href = 'http://localhost:8000';
        })
        .catch((error) => {
            console.error('Registration error:', error);
            let errorMessage = 'Registration failed. ';
            
            switch (error.code) {
                case 'auth/email-already-in-use':
                    errorMessage += 'This email is already registered.';
                    break;
                case 'auth/invalid-email':
                    errorMessage += 'Invalid email address.';
                    break;
                case 'auth/operation-not-allowed':
                    errorMessage += 'Email/password accounts are not enabled.';
                    break;
                case 'auth/weak-password':
                    errorMessage += 'Password is too weak.';
                    break;
                default:
                    errorMessage += error.message;
            }
            
            showError(errorMessage);
            resetButton('register-btn');
        });
}

window.loginWithGoogle = function() {
    console.log('Attempting Google login');
    
    if (typeof auth === 'undefined' || typeof googleProvider === 'undefined') {
        showError('Authentication not initialized. Please refresh the page.');
        return;
    }
    
    auth.signInWithPopup(googleProvider)
        .then((result) => {
            console.log('Google login successful!');
            window.location.href = 'http://localhost:8000';
        })
        .catch((error) => {
            console.error('Google login error:', error);
            showError('Google sign-in failed: ' + error.message);
            resetButton('google-login-btn');
        });
}

// Initialize auth state listener when the page loads
document.addEventListener('DOMContentLoaded', function() {
    if (typeof auth !== 'undefined') {
        auth.onAuthStateChanged((user) => {
            console.log('Auth state changed:', user ? 'User logged in' : 'No user');
            if (user && (window.location.pathname.includes('login.html') || 
                         window.location.pathname.includes('register.html') ||
                         window.location.pathname.endsWith('/') ||
                         window.location.pathname.endsWith('/index.html'))) {
                console.log('User already logged in, redirecting...');
                window.location.href = 'http://localhost:8000';
            }
        });
    } else {
        console.error('Auth not available for state monitoring');
    }
});