from src.data_store import data_store
from src.error import InputError, AccessError

from src.helpers import find_user, update_time_stamp, update_exists, update_user_time_stamp, update_user_exists, condense_message, update_data_store, update_data_p


from src.notification import is_valid_tag, new_notification_tag, new_notification_react

import time
import threading


def message_send(auth_user_id, location_id, message, location_type, message_id, ignore_max_length):
   
    '''
    Send a message from the authorised user to the location
    specified by location_id and a creation_time of time_created.

    Arguments:
        auth_user_id (int)
        location_id (int)
        message (string)
        location_type (string)
        message_id (int)
        ignore_max_length (bool)
    
    Exceptions:
        InputError:
            - Occurs when location_id does not refer to a 
              valid location of location_type.
            - Occurs when length of messsage is less than 1 or 
              over 1000 characters and it is not a standup message
              or message + shared message caption.

        AccessError:
            - Occurs when location_id is valid and the 
              auth_user is not a member of the location
            
    Returns:
        {
            message_id (int)
        }
    '''
    update_data_store()
    store = data_store.get()
    auth_user = find_user(auth_user_id)

    if not ignore_max_length and (len(message) < 1 or len(message) > 1000):
        raise InputError(description=
            "Message must have length 1 - 1000 characters")

    if message_id == None:
        message_id = store['message_num'] + 1
        store['message_num'] += 1

    message_dict = {
        'message_id': message_id,
        'message': message,
        'u_id': auth_user_id,
        'time_created' : time.time(), 
        'reacts': {1:[]},
        'is_pinned': False,
        'tags' : []
    }

    match_location = store[location_type].get(location_id)

    if match_location == None:
        raise InputError(description= f"Invalid {location_type[:-1]}_id")

    if auth_user_id in match_location['members_id']:
        match_location['messages'][ message_dict['message_id']] = message_dict
    else:
        raise AccessError(description= f"User is not member of {location_type[:-1]}.")

    store['messages'][message_dict['message_id']] = {
        'location_type': location_type,
        'location_id': location_id,
        'auth_user_id': auth_user_id
    }    
    auth_user['sent_messages'].add(message_dict['message_id'])

    #update for users stats
    update_time_stamp('message')
    update_exists('message','add')

    update_user_time_stamp('message', auth_user_id)
    update_user_exists('message','add', auth_user_id)
    data_store.set(store)

    found = 0
    tags = []


    while found != -1:
        found = message.find('@', found)
        is_valid_tag(message, found, message_dict['tags'], tags, match_location)
        if found != -1:
            found += 1

    for tag in tags:
        new_notification_tag(auth_user_id, store['handles'].get(tag), message_dict['message_id'], message)

    data_store.set(store)
    update_data_p()
    return {'message_id': message_dict['message_id']}

def message_get_v1(auth_user_id, location_id, start, location_type):
    '''
    Given a location_type with ID location_id that the 
    authorised user is a member of, return up to 50 messages 
    between index "start" and "start + 50". Message with 
    index 0 is the most recent message in the dm. This function
    returns a new index "end" which is the value of "start + 50",
    or, if this function has returned the least recent messages
    in the location, returns -1 in "end" to indicate there
    are no more messages to load after this return. Scheduled
    messages (i.e. those with a creation time in the future) 
    are not included.

    Arguments:
        auth_user_id (int)
        location_id (int)
        start (int)
        location_type (string)
    
    Exceptions:
        InputError:
            - Occurs when location_id does not refer to a valid dm.
            - Occurs when start is greater than the total 
              number of messages in the location.
        AccessError:
            - Occurs when auth_user_id does not refer to a valid user.
            - Occurs when location_id is valid and the
              authorised user is not a member of the location.

    Returns:
        {
            messages[{message_id, u_id, message, time_created}] (list of message dictionaries)
            start (int)
            end (int)
        }
    '''
    store = data_store.get()

    match_location = store[location_type].get(location_id)
    if match_location == None:
        raise InputError(description= f"Invalid {location_type[:-1]}_id")

    if auth_user_id not in match_location['members_id']:
        raise AccessError(description= f"User is not a member of {location_type[:-1]}.")

    if start > len(match_location['messages']):
        raise InputError(description=
            f"Start is greater than the total number of messages in the {location_type[:-1]}.")

    return_messages = []
    i = start
    message_list = list(match_location['messages'].values())
    message_list.reverse()
    while i < min(start + 50, len(message_list)):
        return_messages.append(condense_message(auth_user_id, message_list[i]))
        i += 1

    if start + 50 > len(match_location['messages']):
        end = -1
    else:
       end = start + 50
    
    return {
        'messages': return_messages,
        'start': start,
        'end': end
    }

def message_edit(auth_user_id, message_id, message):
    '''
    Given a message, update its text with new text. 
    If the new message is an empty string, the message is deleted.

    Arguments:
        auth_user_id (int)
        message_id (int)
        message (string)
        is_standup (bool)
    
    Exceptions:
        InputError:
            Occurs when length of message is over 1000 characters.
            Occurs when message_id does not refer to a valid message within a channel/dm
            the user has joined.

        AccessError:
            Occurs when the message_id is valid and the user is a member of the channel/dm and:
            the message wasn't send by the user and the user is not an owner of the channel/dm

    Returns:
        {}
    '''
    store = data_store.get()
    if len(message) > 1000:
        raise InputError(description="Message cannot be longer than 1000 characters.")

    message_data = store['messages'].get(message_id)

    if message_data == None:
        raise InputError(description='Invalid message_id.')

    location_match = store[message_data['location_type']].get(message_data['location_id'])

    if auth_user_id not in location_match['members_id']:
        raise InputError(description=f'User is not a member of the {message_data["location_type"][:-1]}.')

    if message_id in find_user(auth_user_id)['sent_messages']:
        pass
    elif find_user(auth_user_id)[message_data['location_type']][message_data['location_id']] == 1:
        pass
    elif find_user(auth_user_id)['permissions'] == 1:
        pass
    else:
        raise AccessError(description="User lacks permissions to edit message.")

    found = 0
    new_tags = []
    while found != -1:
        found = message.find('@', found)
        is_valid_tag(message, found, location_match['messages'][message_id]['tags'], new_tags, location_match)
        if found != -1:
            found += 1

    for tag in new_tags:
        new_notification_tag(auth_user_id, store['handles'].get(tag), message_id, message)

    found = 0
    tags = []
    while found != -1:
        found = message.find('@', found)
        is_valid_tag(message, found, tags, tags, location_match)
        if found != -1:
            found += 1
    
    if message == '':
        message_remove_v1(auth_user_id, message_id)
    else:
        location_match['messages'][message_id]['message'] = message
        location_match['messages'][message_id]['tags'] = []

def message_remove_v1(auth_user_id, message_id):
    '''
    Given a message_id for a message, this message is removed from the channel/DM
    
    Input:  
        token 
        message_id 

    InputError: 
        message_id does not refer to a valid message within
        a channel/DM that the authorised user has joined

    AccessError: 
        - when message_id refers to a valid message in a 
          joined channel/DM and none of the following are true:
            - the message was sent by the authorised user making this request
            - the authorised user has owner permissions in the channel/DM

    Returns: 
        {} 
    '''

    store = data_store.get()

    message_data = store['messages'].get(message_id)

    if message_data == None:
        raise InputError(description='Invalid message_id.')

    location_match = store[message_data['location_type']].get(message_data['location_id'])

    if auth_user_id not in location_match['members_id']:
        raise InputError(description=f'User is not a member of the {message_data["location_type"][:-1]}.')
    
    if message_id in find_user(auth_user_id)['sent_messages']:
        pass
    elif find_user(auth_user_id)[message_data['location_type']][message_data['location_id']] == 1:
        pass
    elif find_user(auth_user_id)['permissions'] == 1:
        pass
    else:
        raise AccessError(description="User lacks permissions to remove message.")

    del location_match['messages'][message_id]
    store['messages'].pop(message_id)
    #update users stats
    update_time_stamp('message')
    update_exists('message','remove')
    data_store.set(store)
    return {}


def message_react_v1(auth_user_id, message_id, react_id):
    '''
    Given a message within a channel or DM the authorised 
    user is part of, add a "react" to that particular message.

    Arguments:
        auth_user_id (int)
        message_id (int)
        react_id (int)
    
    Exceptions:
        InputError:
            - message_id is not a valid message within a  
              channel or DM that the authorised user has joined

            - react_id is not a valid react ID

            - The message already contains a react  
              with ID react_id from the authorised user

    '''
    store = data_store.get()
    message_data = store['messages'].get(message_id)

    if react_id != 1:
        raise InputError(description='React_id is not a valid react ID')

    if message_data == None:
        raise InputError(description='Invalid message_id.')

    location_match = store[message_data['location_type']].get(message_data['location_id'])
    if auth_user_id not in location_match['members_id']:
        raise InputError(description=f'User is not a member of the {message_data["location_type"][:-1]}.')

    if auth_user_id not in location_match['messages'][message_id]['reacts'][react_id]:
        location_match['messages'][message_id]['reacts'][react_id].append(auth_user_id)
        new_notification_react(auth_user_id, message_id)
    else: 
        raise InputError(description=
            "The message already contains a react with ID react_id from the authorised user")
    
    return {}


def message_unreact_v1(auth_user_id, message_id, react_id):
    '''
    Given a message within a channel or DM the authorised user 
    is part of, remove a "react" to that particular message.

    Arguments:
        auth_user_id (int)
        message_id (int)
        react_id (int)
    
    Exceptions:
        InputError:
            - message_id is not a valid message within a  
              channel or DM that the authorised user has joined

            - react_id is not a valid react ID

            - the message does not contain a react 
              with ID react_id from the authorised user

    Returns:
        {}
    '''
    store = data_store.get()
    
    # Checking if react_id is valid
    if react_id != 1:
        raise InputError(description='React_id is not a valid react ID')
    
    # Checking if message_id is valid
    message_data = store['messages'].get(message_id)
    if message_data == None:
        raise InputError(description='Invalid message_id.')

    # Checking if user exists
    location_match = store[message_data['location_type']].get(message_data['location_id'])
    
    # Checking if user valid
    if auth_user_id not in location_match['members_id']:
        raise InputError(description=
            f'User is not a member of the {message_data["location_type"][:-1]}.')

    # Removing user if no InputError
    if auth_user_id in location_match['messages'][message_id]['reacts'][react_id]:
        location_match['messages'][message_id]['reacts'][react_id].remove(auth_user_id)
    
    else: 
        raise InputError(description=\
            "The message does not contain a react with \
            ID react_id from the authorised user")
    
    return {}

def send_message_later(auth_user_id, location_id, message, location_type, send_time):
    '''

    Sends a message from the authorised user to the location_type 
    specified by location_id automatically at a specified time in the future.
    
    Input:  
        auth_user_id (int) 
        location_id (int)
        message (string)
        location_type (string)
        send_time (int) 

    InputError when: 
        location_id does not refer to a valid location
        length of message is over 1000 characters
        send_time is a time in the past

    AccessError when:
        location_id is valid and the authorised user
        is not a member of the location they are 
        trying to send a message to

    Returns:
        {}
    '''
    
    store = data_store.get()

    match_location = store[location_type].get(location_id)
    if match_location == None:
        raise InputError(description= f"Invalid {location_type[:-1]}_id")

    if auth_user_id not in match_location['members_id']:
        raise AccessError(description= 
            f"User is not a member of {location_type[:-1]}.")

    if time.time() > send_time:
        raise InputError(description= 
            "Must specify time in the future")

    if len(message) > 1000:
        raise InputError(description=
            "Message cannot be longer than 1000 characters.")

    message_id = store['message_num']
    store['message_num']+= 1

    t = threading.Timer(
        round(send_time - time.time()), 
        message_send, 
        args=[auth_user_id, 
        location_id, 
        message, 
        location_type, 
        message_id, 
        False])
        
    t.start()

    data_store.set(store)
    return {
        'message_id' : message_id
    }

def message_share(auth_user_id, og_message_id, message, channel_id, dm_id):
    '''
    Shares a message to either a DM or channel
    - og_message_id is the ID of the original message. 

    - channel_id is the channel that the message is being shared to,
      and is -1 if it is being sent to a DM. 

    - dm_id is the DM that the message is being shared to, 
      and is -1 if it is being sent to a channel. 

    - message is the optional message in addition to the shared message, 
      and will be an empty string '' if no message is given.

    - A new message should be sent to the channel/DM identified by the 
      channel_id/dm_id that contains the contents of both the original 
      message and the optional message. The format does not matter as 
      long as both the original and optional message exist as a substring 
      within the new message

    Inputs: 
        auth_user_id (int) 
        og_message_id (int)
        message (string)
        channel_id (int)
        dm_id (int) 

    InputError 
        - both channel_id and dm_id are invalid
            
        - neither channel_id nor dm_id are -1
            
        - og_message_id does not refer to a valid message within 
        a channel/DM that the authorised user has joined
            
        - length of message is more than 1000 characters

    AccessError: 
        - the pair of channel_id and dm_id are valid (i.e. one is -1, 
        the other is valid) and the authorised user has not joined the 
        channel or DM they are trying to share the message to
    '''

    store = data_store.get()
    input_error = True

    # Input error if neither DM and channel is -1 
    if channel_id != -1 and dm_id == -1 or channel_id == -1 and dm_id != -1:
        input_error = False
    
    if input_error: 
        raise InputError(description="Neither channel_id nor dm_id are -1")

    elif channel_id != -1: 
        location_id = channel_id
        location_type = 'channels'
    else: 
        location_id = dm_id
        location_type = 'dms'    

    match_location = store[location_type].get(location_id)

    # Input error if DM/Channel is valid 
    if match_location == None: 
        raise InputError(description=f"Invalid {location_type[:-1]} id")

    # Access error when the user isn't part of the 
    # channel they are trying to share too
    if auth_user_id not in match_location['members_id']:
        raise AccessError(description=\
            "the pair of channel_id and dm_id are valid (i.e. one is -1, \
            the other is valid) and the authorised user has not joined the \
            channel or DM they are trying to share the message to")

    
    message_info = store['messages'].get(og_message_id)
    if message_info == None: 
        raise InputError(description="og_message_id does not refer to a valid message within\
             a channel/DM that the authorised user has joined")

    if auth_user_id not in store[message_info['location_type']][message_info['location_id']]['members_id']:
        raise InputError(description=\
            "og_message_id does not refer to a valid message within\
             a channel/DM that the authorised user has joined")  


    # Input error when message is longer than 1000 chars 
    if len(message) > 1000 : 
        raise InputError(description="length of message is more than 1000 characters")

    # Adding message to existing message 
    new_message_string = store[message_info['location_type']][message_info['location_id']]['messages'][og_message_id]['message'] + message

    # Send message and return message_id    
    message_dict = message_send(auth_user_id, location_id, new_message_string, location_type, None, True)
    return {'shared_message_id': message_dict['message_id']}

def message_pin_v1(auth_user_id, message_id):
    '''
    Given a message within a channel or DM, mark it as "pinned".

    Arguments:
        auth_user_id (int)
        message_id (int)
    
    Exceptions:
        InputError:
            - message_id is not a valid message within a  
              channel or DM that the authorised user has joined
            - The message already pinned
        AccessError:
            - message_id refers to a valid message in a joined channel/DM
            and the authorised user does not have owner permissions in the channel/DM

    '''
    store = data_store.get()
    message_data = store['messages'].get(message_id)

    if message_data == None:
        raise InputError(description='Invalid message_id.')

    location_match = store[message_data['location_type']].get(message_data['location_id'])

    if auth_user_id not in location_match['members_id']:
        raise InputError(description=
            f'User is not a member of the {message_data["location_type"][:-1]}.')

    if message_id in find_user(auth_user_id)['sent_messages']:
        pass
    elif find_user(auth_user_id)[message_data['location_type']][message_data['location_id']] == 1:
        pass
    elif find_user(auth_user_id)['permissions'] == 1:
        pass
    else:
        raise AccessError(description="User lacks permissions to pin message.")

    if location_match['messages'][message_id]['is_pinned'] == False:
        location_match['messages'][message_id]['is_pinned'] = True
    
    else: 
        raise InputError(description="The message already pinned")
    
    return {}

def message_unpin_v1(auth_user_id, message_id):
    '''
    Given a message within a channel or DM, remove its mark as pinned.

    Arguments:
        auth_user_id (int)
        message_id (int)
    
    Exceptions:
        InputError:
            - message_id is not a valid message within a  
              channel or DM that the authorised user has joined
            - The message already pinned
        AccessError:
            - message_id refers to a valid message in a joined channel/DM
            and the authorised user does not have owner permissions in the channel/DM

    '''
    store = data_store.get()
    message_data = store['messages'].get(message_id)

    if message_data == None:
        raise InputError(description='Invalid message_id.')

    location_match = store[message_data['location_type']].get(message_data['location_id'])

    if auth_user_id not in location_match['members_id']:
        raise InputError(description=
            f'User is not a member of the {message_data["location_type"][:-1]}.')

    if message_id in find_user(auth_user_id)['sent_messages']:
        pass
    elif find_user(auth_user_id)[message_data['location_type']][message_data['location_id']] == 1:
        pass
    elif find_user(auth_user_id)['permissions'] == 1:
        pass
    else:
        raise AccessError(description="User lacks permissions.")

    if location_match['messages'][message_id]['is_pinned'] == True:
        location_match['messages'][message_id]['is_pinned'] = False
    
    else: 
        raise InputError(description="The message is not pinned")
    
    return {}
