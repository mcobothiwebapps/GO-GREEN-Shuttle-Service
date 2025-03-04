from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import sqlite3
import os

app = Flask(__name__)

# ✅ SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Configure Flask-Session to store sessions persistently
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.permanent_session_lifetime = timedelta(minutes=30)

# ✅ Secret Key for Sessions
app.secret_key = os.urandom(24)

# Initialize extensions
db = SQLAlchemy(app)
Session(app)

# ✅ User Model (SQLite)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')

# ✅ Create Database Tables (Run Once)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# ✅ Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ✅ Login User
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import bcrypt  # ✅ Import bcrypt for password hashing

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ✅ Connect to SQLite Database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # ✅ Fetch user details from database
        cursor.execute("SELECT id, password, role FROM user WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, hashed_password, role = user

            # ✅ Verify Password using bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                session['user_id'] = user_id
                session['email'] = email
                session['role'] = role

                flash('Logged in successfully!', 'success')

                # ✅ Redirect based on role
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'driver':
                    return redirect(url_for('driver_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('User not found. Please register first.', 'danger')

    return render_template('login.html')


# ✅ Forgot Password Route (FIXES ERROR)
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash('If this email is registered, a password reset link has been sent.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

# ✅ Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash("User not found. Please log in again.", "danger")
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)

# ✅ Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    drivers = User.query.filter_by(role="driver").all()
    return render_template('admin_dashboard.html', drivers=drivers)

# ✅ Driver Dashboard
@app.route('/driver_dashboard')
def driver_dashboard():
    if 'user_id' not in session or session.get('role') != 'driver':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    return render_template('driver_dashboard.html')

# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ✅ Session Debugging
@app.route('/session_debug')
def session_debug():
    return f"Session Data: {session}"

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
