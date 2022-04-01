from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import condense_user, find_user


def channels_list_v1(auth_user_id):
    """
    Via the data store, open the channels dictionary 
    Search though the channels and find the corresponding
    details with the provided auth_user_id. 
    
    The user may have multiple channels, in that case 
    return multiple channels

    Arguments: 
        auth_user_id (int)

    Returns: 
        channels (list)
    """   
    store = data_store.get()    
    user = find_user(auth_user_id)

    user_channels = []
    
    for channel in user['channels']:
        match_channel = store['channels'].get(channel)
        new_channel = {
            'channel_id': match_channel['channel_id'], 
            'name': match_channel['name']}

        user_channels.append(new_channel)

    return {'channels': user_channels}


def channels_listall_v1():
    '''
    Provide a list of all channels including private 
    channels, (and their associated details)

    Arguments:
        auth_user_id (int)

    Exceptions:
        AccessError: 
            - Occurs when auth_user_id is invalid

    Return Value:
        Return channels(list) 

    '''

    store = data_store.get()
    channels = list(store['channels'].values())
    get_channel = {'channels': []}
    for ch in channels:
        channel_tmp = {}
        channel_tmp['channel_id'] = ch['channel_id']
        channel_tmp['name'] = ch['name']
        get_channel['channels'].append(channel_tmp)
    return get_channel

def append_member_to_list(id, user_list):
    """ 
    append user member id to user_list
    Arguments:
        id (int)
        user_list (list)
    Return Value:
        user_list (list) 
    """
    user_list.append(id)
    return user_list

def channels_create_v1(auth_user_id, name, is_public):
    """ 
    Creates a new channel with the given name that is either a public 
    or private channel. The user who created it automatically joins 
    the channel. For this iteration, the only channel owner is the user
    who created the channel. 
    
    Arguments:
        auth_user_id (int)
        name (string)
        is_public (boolean)

    Exceptions:
        Input Error 
            - length of name is less than 1 or more than 20 characters

    Return Value:
        { channel_id } 

    """
    # check if name is valid or not
    length_name = len(name)
    if length_name < 1 or length_name > 20 :
        raise InputError(description = 
            'Channel name is not between 1 and 20 characters')
    
    store = data_store.get()

    # check if auth_user_id is valid or not
    auth_user = None
    auth_user = find_user(auth_user_id)
    
    channels = store['channels'] 
    channel = {}
    channel['name'] = name
    channel['is_public'] = is_public
    
    owners = []
    channel['owner_id'] = append_member_to_list(auth_user_id, owners)
    members = []
    channel['members_id'] = append_member_to_list(auth_user_id, members)

    channel['owner_members'] = {}
    channel['owner_members'][auth_user_id] = condense_user(auth_user)
    channel['all_members'] = {}
    channel['all_members'][auth_user_id] = condense_user(auth_user)

    channel['messages'] = {}
    channel['standup'] = {
        'is_active' : False,
        'time_finish' : None,
        'creator' : None,
        'messages' : []
    }

    channel_id = len(channels) + 1
    channel['channel_id'] = channel_id
    auth_user['channels'][channel_id] = 1
    channels[channel_id] = channel
    data_store.set(store)

    return {'channel_id' : channel_id}
