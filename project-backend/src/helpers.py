from src.data_store import data_store
import pickle
from datetime import datetime
import re

def email_validity(email):

    '''
    Given an email, returns True if it is in a valid format, or False otherwise.
    Arguments:
        email (string)

    Return Value:
        Returns Match Object if the email is in a valid format.
        Returns None otherwise.

    '''
    email_format = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    
    return re.fullmatch(email_format, email)

def find_user(auth_user_id):
    '''
    Given an auth_user_id, finds and returns the
    associated dictionary from a users list.

    Arguments:
        users [{user}]
        auth_user_id (int)

    Return Value:
        Returns {user}

    '''   
    auth_user = None

    store = data_store.get()
    for user in store['users']:
        if user['u_id'] == auth_user_id:
            auth_user = user

    return auth_user

def condense_user(user):
    '''
    Given a user dict, returns a user dict containing
    only the following keys from the original:
        u_id
        email
        name_first
        name_last
        handle_str

    Arguments:
        user (dict)

    Return Value:
        Return condensed_user (dict)
    '''
    
    return {
    'u_id': user['u_id'], 
    'email': user['email'],
    'name_first': user['name_first'], 
    'name_last': user['name_last'], 
    'handle_str': user['handle_str']
    
    }
   
def condense_message(auth_user_id, message):
    reacts = []
    for react in message['reacts']:
        react_dict = {
            'react_id': react,
            'u_ids': message['reacts'].get(react),
            'is_this_user_reacted': \
                True if auth_user_id in message['reacts'].get(react) else False
        }
    reacts.append(react_dict)
    new_message = {
        'message_id' : message['message_id'],
        'u_id' : message['u_id'],
        'message' : message['message'], 
        'time_created': message['time_created'],
        'reacts': reacts,
        'is_pinned': message['is_pinned']
    }

    return new_message

def name_length_test(name):
    """  
    A name is entered in this module.
    If the name is not between 1 and 50 (it includes 1 and 50) 
    then it will return False.
    Otherwise True would be returned

    Arguments:
        name (string)

    Return Type:
        boolean 
    """
    length_name = len(name)
    if length_name <= 1 or length_name >= 50 :
        return False
    
    return True


def find_remove_user(user_id):
    '''
    Given an user_id, finds and returns the 
    associated dictionary from removed user list.

    Arguments:
        user_id (int)

    Return Value:
        Returns {user}

    '''   
    user_dict = None

    store = data_store.get()
    for user in store['removed_users']:
        if user['u_id'] == user_id:
            user_dict = user

    return user_dict

def check_permissions(user_id):
    """ 
    Returns the permission of the user
    Arguments:
        user_id (int)
    Return Type:
        return (int)
    """    
    permission = None
    store = data_store.get()
    for user in store['users']:
        if user['u_id'] == user_id:
            permission = user['permissions']
    return permission

def update_data_p():
    '''
    Updates data.p file with data in data_store
    
    '''
    f = open("data.p", "wb")
    f.write(pickle.dumps(data_store.get()))
    f.close()

def update_data_store():
    '''
    Attempts to update data_store with data 
    in data.p file. If data.p file does not 
    exist, creates it.

    '''
    try:
        f = open("data.p", "rb")
        store = data_store.get()
        store = pickle.load(f)
        f.close()
        data_store.set(store)

    except:
        update_data_p()
        
def update_time_stamp(name):
    '''
    Given the name (i.e message, channel or dm) 
    it updates the time stamp in the data store
   
    Argument:
        name (string)

    Return:
        timestamp (int -unix timestamp)
    '''
    store = data_store.get()
    time = store['time_stamped']
    now = datetime.now()
    time[name] = now.timestamp()
    data_store.set(store)
    return time[name]

def update_exists(name, action):
    '''
    Given the name (i.e message, channel or dm) 
    and action is with remove or add If the 
    action is 'add' then add 1 otherwise it's minus 1

    Argument:
        name(string)
        action(string)
    '''

    store = data_store.get()
    time = store['time_stamped']
    name_exist = name + '_exists'
    if action == 'add':
        store[name_exist] += 1
    else:
        store[name_exist] -= 1
    
    temp = {
        'num_'+ name +'s_exist' : store[name_exist],
        'time_stamp' : time[name]
    }
    name_dict = name + 's_dict'
    store[name_dict].append(temp)

    data_store.set(store)

def add_stats():
    '''
    Given the name (i.e message, channel or dm)
    When the user is the first User in streams, 
    it updates the respective dictionary
    (i.e channels_dict, dm_dict and messages_dict)
    
    '''
    store = data_store.get()
    time = store['time_stamped']
    # More than one function is being updated with this
    # time so the update_time_stamp function is not used
    now = datetime.now()
    time['channel'] = time['message'] = time['dm'] = now.timestamp()
     #  if channels_dict is empty then add
    if len(store['channels_dict']) == 0 and len(store['users']) == 0:
        channel = {
            'num_channels_exist': 0,
            'time_stamp': time['channel'],
        }
        store['channels_dict'].append(channel)
        dm = {
            'num_dms_exist': 0,
            'time_stamp': time['message'],
        }
        store['dms_dict'].append(dm)
        message = {
            'num_messages_exist': 0,
            'time_stamp': time['dm'],
        }
        store['messages_dict'].append(message)
    data_store.set(store)


def update_user_time_stamp(name, auth_user_id):
    
    store = data_store.get()
    user = find_user(auth_user_id)
    time = user['time_stamped']
    now = datetime.now()
    time[name] = now.timestamp()
    data_store.set(store)
    
    return time[name]

def update_user_exists(name, action, auth_user_id):
    '''
    Given the name (i.e message, channel or dm) and action is with remove or add
    If the action is 'add' then add 1 otherwise it's minus 1
    Argument:
        name(string)
        action(string)
    '''
    store = data_store.get()
    user = find_user(auth_user_id)
    time = user['time_stamped']
    temp = "s_sent" if name == "message" else "s_joined"
    
    name_exist = name + temp
    if action == 'add':
        user[name_exist] += 1
    else:
        user[name_exist] -= 1
    
    temp1 = {
        'num_'+ name + temp : user[name_exist],
        'time_stamp' : time[name]
    }
    name_dict = name + '_dict'
    user[name_dict].append(temp1)
    data_store.set(store)
    

def add_user_stats(auth_user_id):
    '''
    given the user id and update the user's dictionary
    '''
    
    store = data_store.get()
    user = find_user(auth_user_id)
    time = user['time_stamped']
    # More than one function is being updated with this
    # time so the update_time_stamp function is not used
    now = datetime.now()
    
    time['channel'] = time['message'] = time['dm'] = now.timestamp()
        
    channel = {
        'num_channels_joined': 0,
        'time_stamp': time['channel'],
    }
    
    user['channel_dict'].append(channel)
    dm = {
        'num_dms_joined': 0,
        'time_stamp': time['message'],
    }
    user['dm_dict'].append(dm)
    message = {
        'num_messages_sent': 0,
        'time_stamp': time['dm'],
    }
    user['message_dict'].append(message)
    
    data_store.set(store)
    

