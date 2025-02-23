from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
import os
from firebase_config import auth, database

app = Flask(__name__)

# Secure Secret Key
app.secret_key = os.urandom(24)

# Session Expiry Handling (Auto logout after 30 minutes of inactivity)
app.permanent_session_lifetime = timedelta(minutes=30)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session.permanent = True  # Enable session timeout feature
            session['user'] = user['idToken']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Invalid credentials. Please try again.', 'danger')
            print(f"Login Error: {str(e)}")  # Debugging
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validate password length
        if len(password) < 6:
            flash('Password should be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))

        try:
            # Firebase registration logic
            user = auth.create_user_with_email_and_password(email, password)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            print(f"Registration Error: {str(e)}")  # Debugging
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html')
    else:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        try:
            auth.send_password_reset_email(email)
            flash('Password reset email sent!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error sending reset email: {str(e)}', 'danger')
    return render_template('forgot_password.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
