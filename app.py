from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

DATABASE = "expense_tracker.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    # At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    return (len(password) >= 8 and 
            any(c.isupper() for c in password) and 
            any(c.islower() for c in password) and 
            any(c.isdigit() for c in password))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        # Validation
        if not username or not email or not password:
            flash('All fields are required')
            return render_template('signup.html')

        if not is_valid_email(email):
            flash('Invalid email format')
            return render_template('signup.html')

        if not is_valid_password(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, and numbers')
            return render_template('signup.html')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered')
                return render_template('signup.html')

            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                flash('Username already taken')
                return render_template('signup.html')

            # Create new user
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except sqlite3.Error as e:
            flash('An error occurred. Please try again.')
            return render_template('signup.html')
        finally:
            conn.close()

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        if not email or not password:
            flash('Please fill in all fields')
            return render_template('login.html')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('tracker'))
            else:
                flash('Invalid email or password')
                return render_template('login.html')

        except sqlite3.Error as e:
            flash('An error occurred. Please try again.')
            return render_template('login.html')
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/tracker', methods=['GET', 'POST'])
def tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        user_id = session['user_id']

        try:
            cursor.execute('''
                INSERT INTO expenses (user_id, name, date, category, amount) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, date, category, amount))
            conn.commit()
            flash('Expense added successfully!', 'success')
        except sqlite3.Error as e:
            flash('Error adding expense. Please try again.')

    # Fetch expenses for the logged-in user
    cursor.execute('''
        SELECT id, name, date, category, amount 
        FROM expenses 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (session['user_id'],))
    expenses = cursor.fetchall()

    # Calculate total amount
    cursor.execute('''
        SELECT SUM(amount) as total 
        FROM expenses 
        WHERE user_id = ?
    ''', (session['user_id'],))
    total = cursor.fetchone()['total']

    conn.close()
    return render_template('tracker.html', 
                         expenses=expenses, 
                         total_amount=total)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/delete_expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify the expense belongs to the logged-in user
        cursor.execute('''
            DELETE FROM expenses 
            WHERE id = ? AND user_id = ?
        ''', (expense_id, session['user_id']))
        conn.commit()
        return jsonify({'message': 'Expense deleted successfully'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']

        try:
            cursor.execute('''
                UPDATE expenses 
                SET name = ?, date = ?, category = ?, amount = ?
                WHERE id = ? AND user_id = ?
            ''', (name, date, category, amount, expense_id, session['user_id']))
            conn.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('tracker'))
        except sqlite3.Error as e:
            flash('Error updating expense')

    # Get the expense details for editing
    cursor.execute('''
        SELECT * FROM expenses 
        WHERE id = ? AND user_id = ?
    ''', (expense_id, session['user_id']))
    expense = cursor.fetchone()
    conn.close()

    if expense is None:
        flash('Expense not found')
        return redirect(url_for('tracker'))

    return render_template('edit_expense.html', expense=expense)

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())

# Initialize the database when the app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
