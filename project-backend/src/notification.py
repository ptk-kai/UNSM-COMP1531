from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user

def is_valid_tag(message, char, tag_list, new_tag_list, match_location):
    '''
    Checks if a substring starting with @ and ending at the first
    non-alphanumeric character is a valid tag that is not already
    tagged, and if so adds it to a list.

    Arguments:
        message (string)
        char (int)
        tag_list (list)
        new_tag_list (list)
        match_location (dict)
    '''

    if char == -1:
        return 

    tag = ''

    for character in message[char + 1:]:
        if not character.isalnum():
            break
        tag += character

    store = data_store.get()
    if tag in store['handles']\
        and tag not in tag_list\
        and store['handles'].get(tag) in match_location['members_id']:

        tag_list.append(tag)
        new_tag_list.append(tag)
    
    return

def new_notification_invite(inviter_id, invitee, location_id, location_type):
    '''
    Adds a new notification to an invitee who has been invited to a channel or
    dm.

    Arguments:
        inviter_id (int)
        invitee (int)
        location_id (int)
        location_type (string)
    '''

    store = data_store.get()
    inviter = find_user(inviter_id)

    new_notification = {
        'channel_id' : location_id if location_type == 'channels' else -1,
        'dm_id' : location_id if location_type == 'dms' else -1,
        'notification_message' : inviter['handle_str'] 
                                + ' added you to ' + 
                                store[location_type][location_id].get('name')
    }

    auth_user = find_user(invitee)
    auth_user['notifications'].insert(0, new_notification)

    return

def new_notification_react(reacter_id, message_id):
    '''
    Adds a new notification to the creator of a reacted message.

    Arguments:
        reacter_id (int)
        message_id (int)
    '''
    store = data_store.get()
    message = store['messages'].get(message_id)
    reacter = find_user(reacter_id)

    new_notification = {
        'channel_id' : message['location_id'] if message['location_type'] == 'channels' else -1,
        'dm_id' : message['location_id'] if message['location_type'] == 'dms' else -1,
        'notification_message' : reacter['handle_str'] + 
                                ' reacted to your message in ' + 
                                 store[message['location_type']][message['location_id']].get('name')
    }

    auth_user = find_user(message['auth_user_id'])
    auth_user['notifications'].insert(0, new_notification)

    return
    

def new_notification_tag(tagger_id, taggee, message_id, message):
    '''
    Adds a new notification to a user who has been tagged in a message.

    Arguments:
        tagger_id (int)
        taggee (int)
        message_id (int)
        message (string)
    '''

    store = data_store.get()
    message_info = store['messages'].get(message_id)
    tagger = find_user(tagger_id)


    new_notification = {
        'channel_id' : message_info['location_id'] if message_info['location_type'] == 'channels' else -1,
        'dm_id' : message_info['location_id'] if message_info['location_type'] == 'dms' else -1,
        'notification_message' : tagger['handle_str'] + 
                                ' tagged you in ' + 
                                store[message_info['location_type']][message_info['location_id']].get('name') + ': ' + message[0:20]
    }

    auth_user = find_user(taggee)
    auth_user['notifications'].insert(0, new_notification)
    
    return
    
def get_notifications(auth_user_id):
    '''
    Returns a list of a user's 20 most recent notifications. 

    Arguments:
        inviter_id (int)
        invitee (int)
        location_id (int)
        location_type (string)

    Return type:
        {'notifications': []}
    '''
    return {
        'notifications': find_user(auth_user_id)['notifications'][0:20]
        }