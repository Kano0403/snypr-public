from namebase_marketplace.marketplace import *
from accountvar import AccountInfo

from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_mysqldb import MySQL
import datetime

# app = Flask(__name__)
# mysql = MySQL(app)
login_info = AccountInfo()
marketplace = Marketplace(login_info.username, login_info.password)

# Delete variables holding sensitive information
del login_info


def check_names(app, mysql, database_host='localhost', database_user='root', database_password='', database_name='snypr-db1'):
    # # MySQL config
    # app.config['MYSQL_HOST'] = database_host
    # app.config['MYSQL_USER'] = database_user
    # app.config['MYSQL_PASSWORD'] = database_password
    # app.config['MYSQL_DB'] = database_name
    # app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM names WHERE state = %s OR state = %s OR state = %s", ('active', 'reveal', ''))
    names = cur.fetchall()
    cur.close()

    for name in names:
        print(name)

        name_info = marketplace.get_domain_info(name['domain_name'])
        print(name_info)

        if not name_info['bids']:
            makebid = marketplace.create_bid(name['domain_name'], name['increased_buffer'], 0)
            print(makebid)

            # Create cur for updating frontend variables in database
            cur = mysql.connection.cursur()
            cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, date_edited = %s", (
                'active',  # State
                ( int(name_info['height']) - int(name_info['revealBlock'])),  # biddable_blocks
                ( int(name_info['height']) - int(name_info['closeBlock'])),   # total_blocks
                datetime.datetime.utcnow()  # date_edited
            ))
        else:
            print('Bid not needed')
