from functools import wraps

from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, PasswordField, validators

import datetime

from nbintegration import check_names
from accountvar import DatabaseInfo
from data import Names

# Hehehe
app = Flask(__name__)
mysql = MySQL(app)
database_info = DatabaseInfo()

# MySQL config
app.config['MYSQL_HOST'] = database_info.host
app.config['MYSQL_USER'] = database_info.user
app.config['MYSQL_PASSWORD'] = database_info.password
app.config['MYSQL_DB'] = database_info.name
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Delete variables holding sensitive information
del database_info


# ----- WRAPS ----- #

# def is_owner(id):
#    def wrapper(f):
#        @wraps(f)
#        def wrapped(*args, **kwargs):
#            if 'id' in session:
#                if id == session['id']:
#                    return f(*args, **kwargs)
#                else:
#                    flash('Unauthorized')
#            else:
#                pass
#            flash('Unauthorized (Not logged in/session not initialized)', 'danger')
#            return redirect(url_for('login'))
#        return wrapped
#    return wrapper


def is_owner(name_id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM names WHERE id = %s AND owner_id = %s", (name_id, session['id']))
    cur.close()
    if result > 0:
        return True
    return False


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized', 'danger')
            return redirect(url_for('login'))
    return wrap


def is_not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            flash('You are already logged in!', 'success')
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return wrap


def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'is_admin' in session:
            if session['is_admin']:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized', 'danger')
                return redirect(url_for('index'))
        flash('Unauthorized (Not logged in/session not initialized)', 'danger')
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
@is_logged_in
def dashboard():
    # Get names that are owned by current user
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM names WHERE owner_id = %s", (session['id']))
    names = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template('dashboard.html', names=names)
    return render_template('dashboard.html')


class NameInfoForm(Form):
    pass
    # Show Domain Name
    # Show Plan [Potentially add a SUBMIT PLAN CHANGE REQUEST button that will be manually reviewed via a discord.py bot?]
    # Show domain auction info [Incorporate a REPORT button in case it is incorrect]
    # - Auction Stage
    # - Biddable blocks remaining in auction
    # - Total Blocks Remaining in auction
    # - We are the most recent bidder (True/False)
    # Show current PROTECT AFTER field (Default:0, greyed out based on plan)
    # Show INCREASED BUFFER field (Default:0.1, greyed out based on plan)
    protect_after = StringField('Protect After', [
        validators.DataRequired(),
        validators.number_range(0, 720, 'Please enter a valid amount. (0 - 720)')
    ])
    increased_buffer = StringField('Increased Buffer', [
        validators.DataRequired(),
        validators.number_range(1,99, 'Please enter a valid amount. (')
    ])


@app.route('/dashboard/names/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def name(id):
    # Check if logged-in user owns this name
    print(id)
    if not is_owner(id):
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM names WHERE id = %s AND owner_id = %s", (id, session['id']))
    if result == 0:
        flash('Unauthorized - 2', 'danger')
        return redirect(url_for('dashboard'))
    name_info = cur.fetchone()

    print(name_info['state'])
    if name_info['state'] == "":
        flash('This has not been initialized yet. Please come back soon. (Max time until initialization: 5 minutes)', 'danger')
        return redirect(url_for('dashboard'))

    domain_name = name_info['domain_name']
    state = name_info['state']
    biddable_blocks = name_info['biddable_blocks']
    total_blocks = name_info['total_blocks']
    is_most_recent = name_info['is_most_recent']

    protect_after = name_info['protect_after']
    increased_buffer = name_info['increased_buffer']

    form = NameInfoForm(request.form)

    form.protect_after.data = protect_after
    form.increased_buffer.data = increased_buffer

    if request.method == 'POST' and form.validate():
        # Get form info
        protect_after = form.protect_after.data
        increased_buffer = form.increased_buffer.data

        cur = mysql.connection.cursor()
        cur.execute("UPDATE names SET protect_after = %s, increased_buffer = %s, date_edited = %s WHERE id = %s", (protect_after, increased_buffer, datetime.datetime.utcnow(), id))
        mysql.connection.commit()
        cur.close()

        return name(id)
    return render_template('name.html', form=form, domain_name=domain_name, state=state, biddable_blocks=biddable_blocks, total_blocks=total_blocks, is_most_recent=is_most_recent)


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
        owner_id = session['id']
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
        cur.execute("INSERT INTO names(owner_id, domain_name, plan, date_edited) VALUES(%s, %s, %s, %s)", (owner_id, domain_name, plan, datetime.datetime.utcnow()))
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

            if sha256_crypt.verify(password, hashed_password):
                # Set session variables
                session['logged_in'] = True
                session['username'] = username
                session['names'] = names
                session['id'] = str(data['id'])
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
                return redirect(url_for('dashboard'))
            else:
                print('FAIL - INCORRECT PASSWORD')
                error = 'Invalid Login. Please check your username and/or password.'
                return render_template('login.html', error=error)

        else:
            print('FAIL - NO USER')
            error = 'Invalid Login. Please check your username and/or password.'
            return render_template('login.html', error=error)

    # If GET:
    return render_template('login.html')


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Logout Successful', 'success')
    return redirect(url_for('login'))


@app.route('/adminpanel')
@is_admin
def admin_panel():
    print(datetime.datetime.now())
    print(datetime.datetime.utcnow())
    check_names(app, mysql)
    return "Check terminal for output"


if __name__ == '__main__':
    app.secret_key='sectesdfasj;dfakjs;a234283407*(&#(*$&42038470238'
    app.run(debug=True, port=1020, host='127.0.0.1')
    check_names()
