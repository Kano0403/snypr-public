from functools import wraps

from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, PasswordField, validators

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


def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['is_admin']:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized')
            return redirect(url_for('index'))
    return wrap


# ----- MAIN ----- #
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html', names=Names)


@app.route('/dashboard/names/<string:id>')
def name(id):
    return render_template('')


class NameInitiationForm(Form):
    domain_name = StringField('Domain', [validators.DataRequired()])
    plan = StringField('Plan', [validators.AnyOf(values=['Regular', 'Pro', 'Elite'], message='Please choose a plan based on the list of available plans: Regular, Pro, Elite')])


@app.route('/initiate_name', methods=['GET', 'POST'])
@is_logged_in
def initiate_name():
    form = NameInitiationForm(request.form)
    if request.method == 'POST' and form.validate():
        domain_name = form.domain_name.data
        plan = form.plan.data
        owners_id = session['id']
        # state = NAMEBASE API REQUEST
        # blocks_in_auction = NAMEBASE API REQUEST
        # blocks_in_reveal = NAMEBASE API REQUEST

        # Cursor
        cur = mysql.connection.cursor()

        # -- Check to see if name exists -- #
        # Get names matching
        result = cur.execute("SELECT * FROM names WHERE domain_name = %s", [domain_name])
        if result > 0:
            cur.close()
            flash('This name has already been initialized. Please make sure everything is spelled correctly, otherwise consider this name taken.', 'danger')
            return redirect(url_for('initiate_name'))
        # Execute
        cur.execute("INSERT INTO names(owners_id, domain_name, plan) VALUES(%s, %s, %s)", (owners_id, domain_name, plan))

        # ----- TODO: append to user's "names" value in the "users" database to show ownership of this name.
        names = cur.execute("SELECT * FROM users WHERE id = session['id']")
        result = cur.execute("SELECT * FROM names WHERE domain_name = %s", [domain_name])
        print(names)
        names += f"{result['id']},"
        print(names)
        # Commit
        mysql.connection.commit()
        # Close
        cur.close()

        # Flash
        flash('Name Initialized', 'success')

        return redirect(url_for('dashboard'))
    return render_template('initiate_name.html', form=form)

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
                session['id'] = data['id']
                print(session['username'])
                print(session['names'])
                print(session['id'])
                print(session['logged_in'])
                print(data['is_admin'])
                if data['is_admin'] == 1:
                    session['is_admin'] = True
                else:
                    session['is_admin'] = False
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
@is_logged_in
def logout():
    session.clear()
    flash('Logout Successful', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key='sectesdfasj;dfakjs;a234283407*(&#(*$&42038470238'
    app.run(debug=True, port=1020, host='127.0.0.1')
