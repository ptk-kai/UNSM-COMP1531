import threading
from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user, update_data_store, update_data_p
from src.message import message_send
import time

def is_standup_active(auth_user_id, channel_id):
    '''
    For a given channel, returns whether a standup is active 
    in it, and what time the standup finishes. If no standup 
    is active, then time_finish returns None.

    Arguments:
        auth_user_id (int)
        channel_id (int)

    Exceptions:
        InputError:
            channel_id does not refer to a valid channel
        AccessError:
            channel_id is valid and the authorised user 
            is not a member of the channel
            
    Returns:
        {
            is_active (bool),
            time_finish (int)
        }
    '''
    store = data_store.get()

    match = store['channels'].get(channel_id)
    if match == None:
        raise InputError(description="Invalid channel_id")
    
    if auth_user_id not in match['members_id']:
        raise AccessError(description=
            "User is not member of channel.")
    

    return {
        'is_active': match['standup'].get('is_active'),
        'time_finish' : match['standup'].get('time_finish')
    }

def clear_standup(match):
    '''
    Resets a channel's standup fields to default.

    Arguments:
        match (dict)

    '''

    match['standup']['is_active'] = False
    match['standup']['time_finish'] = None
    match['standup']['creator'] = None
    match['standup']['messages'] = []
    update_data_p()


#triggered at end of standup
def end_standup(channel_id):
    '''
    Posts the messages in the standup queue, 
    formatted as a standup message.

    Arguments:
        channel_id (int)

    '''

    store = data_store.get()
    match = store['channels'].get(channel_id)
    
    standup_message = ''
    for message in match['standup']['messages']:
        standup_message += find_user(message['auth_user_id']).get('handle_str')
        standup_message += ': '
        standup_message += message['message']
        standup_message += '\n'

    creator = match['standup']['creator']
    clear_standup(match)
    update_data_p()

    if standup_message != '':
        message_send(creator, channel_id, standup_message[:-1], 'channels', None, True)

    update_data_p()



def start_standup(auth_user_id, channel_id, length):
    '''
    For a given channel, start the standup period.
    "length" is an integer that denotes the number 
    of seconds that the standup occurs for.

    Arguments:
        auth_user_id (int)
        channel_id (int)
        length (int)

    Exceptions:
        InputError:
            - channel_id does not refer to a valid channel
            - length is a negative integer
            - an active standup is currently running in the channel
        AccessError:
            - channel_id is valid and the authorised 
              user is not a member of the channel
            
    Returns:
        {
            time_finish (int)
        }
    '''

    start_time = time.time()
    store = data_store.get()
    match = store['channels'].get(channel_id)

    if match == None:
        raise InputError(description="Invalid channel_id")
    
    if auth_user_id not in match['members_id']:
        raise AccessError(description="User is not member of channel.")
    
    if length < 0:
        raise InputError(description="Length must be non-negative integer.")

    if is_standup_active(auth_user_id, channel_id).get('time_finish') != None:
        raise InputError(description="Standup already active in channel") 

    
    match['standup']['is_active'] = True
    match['standup']['time_finish'] = round(start_time + length)
    match['standup']['creator'] = auth_user_id

    t = threading.Timer(length, end_standup, args=[channel_id])
    t.start()

    data_store.set(store)
    return {'time_finish': round(start_time + length)}
    

def send_message_standup(auth_user_id, channel_id, message):
    '''
    Adds a message to the standup message queue.

    Arguments:
        auth_user_id (int)
        channel_id (int)
        message (string)

    Exceptions:
        InputError:
            channel_id does not refer to a valid channel
            length of message is over 1000 characters
            an active standup is not currently running in the channel
        AccessError:
            channel_id is valid and the authorised
            user is not a member of the channel
            
    Returns:
        {}
    '''

    store = data_store.get()
    match = store['channels'].get(channel_id)

    if match == None:
        raise InputError(description="Invalid channel_id")
    
    if auth_user_id not in match['members_id']:
        raise AccessError(description="User is not member of channel.")
    
    if len(message) > 1000:
        raise InputError(description="Message must be less than 1000 characters")

    if is_standup_active(auth_user_id, channel_id).get('time_finish') == None:
        raise InputError(description="Standup not active in channel") 


    new_standup_message = {
        'auth_user_id': auth_user_id,
        'message' : message
    }
    match['standup']['messages'].append(new_standup_message)
    return {}
