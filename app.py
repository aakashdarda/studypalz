import os
import mysql.connector
from mysql.connector import Error
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = '1234'  # Change this to a random secret key

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Use 'root' if that's your default MySQL user
    'password': '',  # Leave blank if no password, or enter your password
    'auth_plugin': 'mysql_native_password'  # Add this line to resolve authentication issue
}

# Database initialization function
def init_db():
    try:
        # Establish connection without specifying database first
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            auth_plugin=DB_CONFIG['auth_plugin']
        )
        
        # Create cursor
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS studypalzlogin")
        cursor.execute("USE studypalzlogin")

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                grade VARCHAR(20) NOT NULL
            )
        ''')

        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()

    except Error as err:
        print(f"Error during database initialization: {err}")

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database connection helper
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='studypalz_db',
            auth_plugin=DB_CONFIG['auth_plugin']
        )
        return conn
    except Error as err:
        print(f"Error connecting to MySQL Database: {err}")
        return None

# Route for login page
@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

# Route for register page
@app.route('/register')
def register():
    return render_template('register.html')

# Login route
@app.route('/login', methods=['POST'])
def login_process():
    email = request.form['email']
    password = hash_password(request.form['password'])

    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('login'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()

        if user:
            # Successful login
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Failed login
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
    except Error as err:
        print(f"Database error: {err}")
        flash('An error occurred', 'error')
        return redirect(url_for('login'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Registration route
@app.route('/register', methods=['POST'])
def register_process():
    username = request.form['username']
    email = request.form['email']
    password = hash_password(request.form['password'])
    grade = request.form['grade']

    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('register'))

    try:
        cursor = conn.cursor()
        # Check if username or email already exists
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))

        # Insert new user
        cursor.execute(
            'INSERT INTO users (username, email, password, grade) VALUES (%s, %s, %s, %s)', 
            (username, email, password, grade)
        )
        conn.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    except Error as err:
        print(f"Database error: {err}")
        flash('Registration failed', 'error')
        return redirect(url_for('register'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Dashboard route (example)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    return f"Welcome {session['username']}! This is your dashboard."

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)