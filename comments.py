"""
# --- LINE 49 of nbintegration.py
        # # Check if name has been initialized, and if not initialize it
        # if not name_info['bids']:
        #     print("Name not initialized")
        #     bid = name['increased_buffer']
        #     make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
        #     print(f"NB-create_bid: {make_bid}")
        #
        #     # Check if the request went through
        #     if not make_bid['success']:
        #         return make_bid['code']
        #
        #     name_info = marketplace.get_domain_info(name['domain_name'])
        #
        #     if name_info['closeBlock'] is None:
        #         # Update database for frontend
        #         update_names(mysql, 'active', int(bid))
        #         # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
        #         #     'active',  # State
        #         #     -1,  # biddable_blocks
        #         #     -1,  # total_blocks
        #         #     (int(bid)),  # current_bid
        #         #     datetime.datetime.utcnow()  # date_edited
        #         # ))
        #         # cur.close()
        #         return "Not Ready"
        #
        #     # Update database for frontend
        #     update_names(mysql, 'active', int(bid), biddable_blocks=int(name_info['height']) - int(name_info['revealBlock']), total_blocks=int(name_info['height']) - int(name_info['closeBlock']))
        #     # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
        #     #     'active',                                                    # State
        #     #     (int(name_info['height']) - int(name_info['revealBlock'])),  # biddable_blocks
        #     #     (int(name_info['height']) - int(name_info['closeBlock'])),   # total_blocks
        #     #     (int(bid)),                                                  # current_bid
        #     #     datetime.datetime.utcnow()                                   # date_edited
        #     # ))
        #     # cur.close()
        #
        #     return marketplace.get_domain_info(name['domain_name'])
        #
        # print('Name Already Initialized')
        #
        # for each in name_info['bids']:
        #     print(f"Stake: {each['stake_amount']}")
        #     print(f"is_own: {each['is_own']}")
        #
        # new_bid_info = is_highest(name_info['bids'])
        #
        # if new_bid_info['is_bid_needed']:
        #     print(f"Bid of {new_bid_info['highest_bid']} + buffer({name['increased_buffer']}) Needed")
        #     # TODO: Create process of making the new bid
        #     # Create bid increasing by
        #     bid = (new_bid_info['highest_bid'] + name['increased_buffer'])
        #     make_bid = marketplace.create_bid(name['domain_name'], bid, 0)
        #     print(f"NB-create_bid: {make_bid}")
        #
        # else:
        #     print(f"Bid Not Needed")

"""
"""
# --- LINE 65 of nbintegration.py
            # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
            #     'active',  # State
            #     -1,  # biddable_blocks
            #     -1,  # total_blocks
            #     (int(bid)),  # current_bid
            #     datetime.datetime.utcnow()  # date_edited
            # ))
            # cur.close()
"""
"""
# --- LINE 72 of nbintegration.py
        # cur.execute("UPDATE names SET state = %s, biddable_blocks = %s, total_blocks = %s, current_bid = %s, date_edited = %s", (
        #     'active',                                                    # State
        #     (int(name_info['height']) - int(name_info['revealBlock'])),  # biddable_blocks
        #     (int(name_info['height']) - int(name_info['closeBlock'])),   # total_blocks
        #     (int(bid)),                                                  # current_bid
        #     datetime.datetime.utcnow()                                   # date_edited
        # ))
        # cur.close()
"""
"""

"""