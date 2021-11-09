from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from data import Names

Names = Names()
app = Flask(__name__)
mysql = MySQL(app)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'SNYPR-DB1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


# ----- WRAPS ----- #
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized')
            return redirect(url_for('login'))
    return wrap


# ----- MAIN ----- #
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/dashboard')
def dashboard():
    if not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('dashboard.html', names=Names)


class RegisterForm(Form):
    username = StringField('Name', [validators.Length(min=1, max=30)])
    email = StringField('Email', [validators.Length(min=3, max=100)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=64),
        validators.DataRequired(),
        validators.EqualTo('confirmPassword', message='Passwords do not match.')
    ])
    confirmPassword = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        # Register user
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.hash(form.password.data)

        # Create cursor
        cur = mysql.connection.cursor()
        # Execute
        cur.execute("INSERT INTO users(username, email, password) VALUES(%s, %s, %s)", (username, email, password))
        # Commit
        mysql.connection.commit()
        # Close
        cur.close()

        flash('You have been registered. You can now sign in.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cursor
        cur = mysql.connection.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get password
            data = cur.fetchone()
            hashed_password = data['password']
            names = data['names_ids']

            flash('Login Successful')
            redirect(url_for('dashboard'))
            if sha256_crypt.verify(password, hashed_password):
                # Set session variables
                session['logged_in'] = True
                session['username'] = username
                session['names'] = names
                print('PASS')
            else:
                print('FAIL - INCORRECT PASSWORD')
                error = 'Invalid Login. Please check your username and/or password.'
                return render_template('login.html', error=error)

        else:
            print('FAIL - NO USER')
            error = 'Invalid Login. Please check your username and/or password.'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout Successful', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key='sectesdfasj;dfakjs;a234283407*(&#(*$&42038470238'
    app.run(debug=True, port=8000, host='127.0.0.1')
