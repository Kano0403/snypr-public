from operator import itemgetter

from namebase_marketplace.marketplace import *
from accountvar import AccountInfo

from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_mysqldb import MySQL
import datetime

login_info = AccountInfo()
marketplace = Marketplace(namebase_cookie=login_info.cookie)

# Delete variables holding sensitive information
del login_info


def check_names(mysql, database_host='localhost', database_user='root', database_password='', database_name='snypr-db1'):
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

    names = sorted(names, key=itemgetter('biddable_blocks'))
    print(names)
    print()

    # Repeat for each name in the database
    for name in names:
        print("-----------------")
        print(f"Name: {name}")

        name_info = marketplace.get_domain_info(name['domain_name'])
        print(f"NB-domain_info: {name_info}")

        # Check if name has been initialized, and if not initialize it
        if not name_info['bids']:
            print("Name not initialized")
            bid = name['increased_buffer']
            make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
            print(f"NB-create_bid: {make_bid}")

            # Check if the request went through
            if not make_bid['success']:
                return make_bid['code']

            name_info = marketplace.get_domain_info(name['domain_name'])

            if name_info['closeBlock'] is None:
                # Update database for frontend
                update_names(mysql, 'active', int(bid))
                # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
                #     'active',  # State
                #     -1,  # biddable_blocks
                #     -1,  # total_blocks
                #     (int(bid)),  # current_bid
                #     datetime.datetime.utcnow()  # date_edited
                # ))
                # cur.close()
                return "Not Ready"

            # Update database for frontend
            update_names(mysql, 'active', int(bid), biddable_blocks=int(name_info['height']) - int(name_info['revealBlock']), total_blocks=int(name_info['height']) - int(name_info['closeBlock']))
            # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
            #     'active',                                                    # State
            #     (int(name_info['height']) - int(name_info['revealBlock'])),  # biddable_blocks
            #     (int(name_info['height']) - int(name_info['closeBlock'])),   # total_blocks
            #     (int(bid)),                                                  # current_bid
            #     datetime.datetime.utcnow()                                   # date_edited
            # ))
            # cur.close()

            return marketplace.get_domain_info(name['domain_name'])

        print('Name Already Initialized')

        for each in name_info['bids']:
            print(f"Stake: {each['stake_amount']}")
            print(f"is_own: {each['is_own']}")

        new_bid_info = is_highest(name_info['bids'])

        if new_bid_info['is_bid_needed']:
            print(f"Bid of {new_bid_info['highest_bid']} + buffer({name['increased_buffer']}) Needed")
            # TODO: Create process of making the new bid
            # Create bid increasing by
            bid = (new_bid_info['highest_bid'] + name['increased_buffer'])
            make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
            print(f"NB-create_bid: {make_bid}")

        else:
            print(f"Bid Not Needed")

    return "Success"


def is_highest(bids):
    num_bids = len(bids)

    bids = sorted(bids, key=itemgetter('stake_amount'), reverse=True)
    print(f"Bids: {bids}")

    # Check if highest bid is not ours, Check if top bids are equal and both ours
    if len(bids) > 1:
        if bids[0]['stake_amount'] == bids[1]['stake_amount'] and (bids[0]['is_own'] and bids[1]['is_own']):
            return {"is_bid_needed": False}
    else:
        if bids[0]['is_own']:
            return {"is_bid_needed": False}
    return {"is_bid_needed": True, "highest_bid": (int(bids[0]['stake_amount'])/1000000)}


def update_names(mysql, state, bid, biddable_blocks=-1, total_blocks=-1):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
        state,  # State
        int(biddable_blocks),  # biddable_blocks
        int(total_blocks),  # total_blocks
        int(bid),  # current_bid
        datetime.datetime.utcnow()  # date_edited
    ))
    cur.close()


def set_auth(mysql):
    global marketplace
    cur = mysql.connection.cursor()
    cur.execute("SELECT cookie FROM users WHERE id = %s", [session['id']])
    cookie = cur.fetchone()['cookie']
    if cookie is None:
        return "Please add a cookie to your account"
    return cookie
    # marketplace = Marketplace(namebase_cookie=cookie)
