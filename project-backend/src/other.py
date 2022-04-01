from src.data_store import data_store
from src.error import InputError
from src.helpers import find_user, condense_message

def clear_v1():
    store = data_store.get()
    store['users'] = []
    store['handles'] = {}
    store['channels'] = {}
    store['messages'] = {}
    store['dms'] = {}
    store['removed_users'] = []
    store['session_num'] = 0
    store['message_num'] = 0
    store['dm_num'] = 0
    store['active_sessions'] = {}
    store['admin_num'] = 0
    store['pass_reset_codes'] = {}
    store['time_stamped'] = {
        'channels': 0,
        'messages': 0,
        'dms': 0,
    }
    store['channel_exists'] = 0
    store['dm_exists'] = 0
    store['message_exists'] = 0
    store['channels_dict'] = []
    store['dms_dict'] = []
    store['messages_dict'] = []
    
    data_store.set(store)
    return {}

def search_v1(auth_user_id, query_str):
    '''
    Given a query string, return a collection of messages
    in all of the channels/DMs that the user has joined that contain the query.
    Input: auth_user_id, query_str
    Ouput: messages
    InputError when:
        length of query_str is less than 1 or over 1000 characters
    '''
    if len(query_str) < 1 or len(query_str) > 1000:
        raise InputError(description='Invalid query string')
    store = data_store.get()
    auth_user = find_user(auth_user_id)
    match_message = []
    for channel_id in auth_user['channels']:
        match_channel = store['channels'].get(channel_id)
        message_list = list(match_channel['messages'].values())
        #message_list.sort(reverse = True, key = message_sort)
        for i in range(0, len(message_list)):
            if query_str in message_list[i]['message']:
                match_message.append(condense_message(auth_user_id, message_list[i]))
    for dm_id in auth_user['dms']:
        match_dm = store['dms'].get(dm_id)
        message_list = list(match_dm['messages'].values())
        #message_list.sort(reverse = True, key = message_sort)
        for i in range(0, len(message_list)):
            if query_str in message_list[i]['message']:
                match_message.append(condense_message(auth_user_id, message_list[i]))
    return {'messages': match_message}

    