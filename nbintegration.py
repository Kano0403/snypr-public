import collections
from operator import itemgetter

from namebase_marketplace.marketplace import *
from accountvar import AccountInfo

from flask import session
from flask_mysqldb import MySQL
import datetime

login_info = AccountInfo()
marketplace = Marketplace()  # namebase_cookie=login_info.token)

# Hehe
# Delete variables holding sensitive information
del login_info


def check_names(mysql: MySQL) -> dict:  # , database_host: str = 'localhost', database_user: str = 'root', database_password: str = '', database_name: str = 'snypr-db1') -> dict:
    # # MySQL config
    # app.config['MYSQL_HOST'] = database_host
    # app.config['MYSQL_USER'] = database_user
    # app.config['MYSQL_PASSWORD'] = database_password
    # app.config['MYSQL_DB'] = database_name
    # app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM names WHERE state = %s OR state = %s OR state = %s OR state = %s", ('active', 'reveal', 'new', ''))
    names = cur.fetchall()
    cur.close()

    names = sorted(names, key=itemgetter('biddable_blocks'))
    print(names)
    print(marketplace.get_user_info())

    results = {"start_time": datetime.datetime.utcnow()}

    # Repeat for each name in the database
    for name in names:
        print("-----------------")
        print(f"Name: {name}")
        # print(f"User ID: {name['owner_id']}")

        set_auth(mysql, name['owner_id'])
        # print(f"Auth: {marketplace.get_user_info()}")

        name_info = marketplace.get_domain_info(name['domain_name'])
        print(f"NB-domain_info: {name_info}")

        # Add results of the bidder to the final results
        results[name['id']] = name_bidder(mysql, name)
        print(results[name['id']])
        set_auth(mysql, clear=True)
        # ENT-1 comments.py

    # Define the time that it took to complete all checks.
    # results['total_time'] = results['start_time'] - datetime.datetime.utcnow()

    # Define the time that the function ended.
    results['end_time'] = datetime.datetime.utcnow()

    with open('logs/check_names-cycles.txt', 'r+') as cycle_logs:
        cycle_logs.write(f'{str(results)}\n')
    print(results)

    return results


def name_bidder(mysql: MySQL, name: dict) -> object:
    name_info = marketplace.get_domain_info(name['domain_name'])

    # Check if name has been initialized, and if not initialize it
    if not name_info['bids']:
        # print("Name not initialized")
        bid = name['increased_buffer']
        make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
        print(f"NB-create_bid: {make_bid}")

        # Check if the request went through
        try:
            make_bid['success']
        except KeyError:
            return {"code": "s401", "message": make_bid['code'], "success": False}

        # This does not belong here...
        # if name_info['closeBlock'] is None:
        #     # Update database for frontend
        #     update_names(mysql, name['id'], 'active', int(bid))
        #     # ENT-2 comments.py
        #     return {"code": "s402", "message": "Waiting for name auction to begin.", "success": False}

        # Update database for frontend
        update_names(mysql, name['id'], 'active', int(bid))
        # ENT-3 comments.py

        return {"code": "s000", "message": marketplace.get_domain_info(name['domain_name']), "success": True}

    print('Name Already Initialized')

    if not name_info['openBlock'] is None:
        if name_info['height'] >= name_info['closeBlock']:
            update_names(mysql, name['id'], 'finalized', name['current_bid'],
                         biddable_blocks=int(name_info['height']) - int(name_info['revealBlock']),
                         total_blocks=int(name_info['height']) - int(name_info['closeBlock']))
            return {"code": "s403-b", "message": "Name auction ended.", "success": True}
        elif name_info['height'] >= name_info['revealBlock']:
            if not name['state'] == 'reveal':
                update_names(mysql, name['id'], 'reveal', name['current_bid'],
                             total_blocks=int(name_info['height']) - int(name_info['closeBlock']))
            return {"code": "s403-a", "message": "Name is in reveal.", "success": True}

    # Print name bids to console
    # for each in name_info['bids']:
    #     print(f"Stake: {each['stake_amount']}")
    #     print(f"is_own: {each['is_own']}")

    new_bid_info = is_highest(name_info['bids'])

    if new_bid_info['is_bid_needed']:
        print(f"Bid of {new_bid_info['highest_bid']} + buffer({name['increased_buffer']}) Needed")
        # TODO: Create process of making the new bid
        # Create bid increasing by
        bid = (new_bid_info['highest_bid'] + name['increased_buffer'])
        make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
        print(f"NB-create_bid: {make_bid}")

        try:
            make_bid['success']
        except KeyError:
            return {"code": "s401", "message": make_bid['code'], "success": False}

        return {"code": "s000", "message": make_bid, "success": True}

    else:
        print(f"Bid Not Needed")


def is_highest(bids: collections.Iterable) -> dict:
    for bid in bids:
        bid['stake_amount'] = int(bid['stake_amount'])

    bids = sorted(bids, key=itemgetter('stake_amount'), reverse=True)
    # print(f"Bids: {bids}")

    # Check if highest bid is not ours, Check if top bids are equal and both ours
    if len(bids) > 1:
        # Checks if top bids are tied and if so, it checks if both are ours.
        if bids[0]['stake_amount'] == bids[1]['stake_amount'] and (bids[0]['is_own'] and bids[1]['is_own']):
            return {"is_bid_needed": False}
    # Checks if top bid in ours
    if bids[0]['is_own']:
        return {"is_bid_needed": False}
    return {"is_bid_needed": True, "highest_bid": (int(bids[0]['stake_amount']) / 1000000)}


def update_names(mysql: MySQL, id_un: int, state: str, bid: int, biddable_blocks: int = -1,
                 total_blocks: int = -1) -> None:
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s WHERE id = %s",
        (
            state,  # State
            int(biddable_blocks),  # biddable_blocks
            int(total_blocks),  # total_blocks
            int(bid),  # current_bid
            datetime.datetime.utcnow(),  # date_edited
            id_un  # ID of name in database
        ))
    mysql.connection.commit()
    cur.close()


def set_auth(mysql: MySQL, id_sa: int = None, use_session: bool = False, clear: bool = False) -> object:
    global marketplace
    # cookie = None
    cur = mysql.connection.cursor()

    if id_sa is None and not use_session and not clear:
        clear = True

    if clear:
        marketplace = Marketplace()
        return {"code": "s000", "message": "Auth cleared", "success": True}

    if use_session:
        id_sa = session['id']

    cur.execute("SELECT cookie FROM users WHERE id = %s", [id_sa])
    cookie = cur.fetchone()['cookie']

    marketplace = Marketplace(namebase_cookie=cookie)

    user_info = marketplace.get_user_info()
    try:
        if user_info['verificationStatus'] == 'VERIFIED':
            pass
        else:
            return {"code": "s502", "message": "Invalid Cookie", "success": False}
    except KeyError:
        return {"code": "s502", "message": "Invalid Cookie", "success": False}

    return {"code": "s000", "message": f"Auth set: {user_info}", "success": True}
