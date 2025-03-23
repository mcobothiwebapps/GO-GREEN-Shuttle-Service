from flask import Flask, render_template, redirect, url_for, request, flash, session
import sqlite3
import bcrypt
from database import create_tables, create_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'

create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, hashed_pw))
            conn.commit()
            conn.close()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')
@app.route('/admin')
def admin_dashboard():
    conn = create_connection()
    cursor = conn.cursor()

    # Fetch customers who never submitted or were declined
    cursor.execute("""
        SELECT * FROM users
        WHERE id NOT IN (
            SELECT user_id FROM driver_requests WHERE status = 'Approved'
        )
    """)
    customers = cursor.fetchall()

    # Fetch approved drivers with license and status
    cursor.execute("""
        SELECT u.username, u.email, d.license, d.status 
        FROM users u
        JOIN driver_requests d ON u.id = d.user_id
        WHERE d.status = 'Approved'
    """)
    drivers = cursor.fetchall()

    # ✅ This makes sure the latest (resubmitted) request shows up
    cursor.execute("""
        SELECT d.id, d.user_id, d.license, d.vehicle, d.status, u.username, u.email
        FROM driver_requests d
        JOIN users u ON u.id = d.user_id
        WHERE d.status = 'pending'
        AND d.id = (
            SELECT MAX(id) FROM driver_requests WHERE user_id = d.user_id
        )
        ORDER BY d.id DESC
    """)
    pending_requests = cursor.fetchall()

    conn.close()
    return render_template("admin.html", customers=customers, drivers=drivers, pending_requests=pending_requests)


@app.route('/admin/pending_requests')
def pending_requests():
    conn = create_connection()
    cursor = conn.cursor()
    
    # ✅ Fetch only the latest pending request per user
    cursor.execute("""
        SELECT dr.id, u.username, u.email, dr.license, dr.vehicle, dr.status
        FROM driver_requests dr
        JOIN users u ON dr.user_id = u.id
        WHERE dr.status = 'Pending'
        AND dr.id = (
            SELECT MAX(id) FROM driver_requests
            WHERE user_id = dr.user_id AND status = 'Pending'
        )
        ORDER BY dr.id DESC
    """)
    
    pending = cursor.fetchall()
    conn.close()

    return render_template('pending_requests.html', pending=pending)


@app.route('/admin/update_driver_status/<int:request_id>', methods=['POST'])
def update_driver_status(request_id):
    new_status = request.form['status']
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE driver_requests SET status = ? WHERE id = ?", (new_status, request_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        admin_email = 'admin@shuttle.com'
        admin_password = 'admin@123'
        if email == admin_email and password.decode() == admin_password:
            session['user_id'] = 0
            session['username'] = 'Admin'
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = False
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/ride_request')
def ride_request():
    if 'user_id' not in session:
        flash('You must be logged in.', 'warning')
        return redirect(url_for('login'))
    return render_template('ride_request.html')

@app.route('/submit_driver_request', methods=['POST'])
def submit_driver_request():
    if 'user_id' not in session:
        flash("Please log in to request to be a driver.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    license = request.form['license']
    vehicle = request.form['vehicle']

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO driver_requests (user_id, license, vehicle, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, license, vehicle, 'pending'))

    conn.commit()
    conn.close()

    flash("Driver request submitted successfully!", "info")
    return redirect(url_for('dashboard'))

@app.route('/resubmit_driver_request', methods=['POST'])
def resubmit_driver_request():
    if 'user_id' not in session:
        flash("Please log in to resubmit a driver request.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    license = request.form['license']
    vehicle = request.form['vehicle']

    conn = create_connection()
    cursor = conn.cursor()

    # FIX: Case-insensitive match for declined status
    cursor.execute("""
        DELETE FROM driver_requests
        WHERE user_id = ? AND LOWER(status) = 'declined'
    """, (user_id,))

    # Reinsert with pending status
    cursor.execute("""
        INSERT INTO driver_requests (user_id, license, vehicle, status)
        VALUES (?, ?, ?, 'pending')
    """, (user_id, license, vehicle))

    conn.commit()
    conn.close()

    flash("Driver request resubmitted successfully!", "info")
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM rides WHERE user_id = ?", (user_id,))
    rides = cursor.fetchall()

    cursor.execute("SELECT * FROM driver_requests WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    driver_request = cursor.fetchone()

    conn.close()

    return render_template("user_dashboard.html", user=user, rides=rides, driver_request=driver_request)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)