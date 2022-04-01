from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import condense_user, find_user, check_permissions
from src.notification import new_notification_invite

def channel_invite_v1(auth_user_id, channel_id, u_id):
    """ 
    Invites a user with ID u_id to join a channel
    with ID channel_id. Once invited, the user is 
    added to the channel immediately. In both public
    and private channels, all members are able to 
    invite users. 
    
    Arguments :
        auth_user_id (int)
        channel_id (int)
        u_id (int)
    
    Exceptions :
        Input Error:
            - channel_id does not refer to a valid channel
            - u_id does not refer to valid user
            - u_id refers to a user who is already
              a member of the channel
        
        AccessError: 
            - channel_id is valid and the authorised
              user is not a member of the channel 

    Return Value :
        {} (dictionary)
    """
    
    store = data_store.get()

    match_channel = store['channels'].get(channel_id)
    if match_channel == None:
        raise InputError(description = 
            "Channel does not exist")

    auth_user = find_user(auth_user_id)
    if auth_user['channels'].get(channel_id) == None:
        raise AccessError(description = 
            'auth_user is not a member of the channel')

    # Tests if u_id is valid
    valid_user = find_user(u_id)
    if valid_user == None:
        raise InputError(description = 
            'u_id is not valid user' )

    if valid_user['channels'].get(channel_id) != None:
        raise InputError(description = 
            'u_id is already a existing member')
        
    # add u_id to members_id
    match_channel['members_id'].append(u_id)
    match_channel['all_members'][u_id] = condense_user(valid_user)
    valid_user['channels'][channel_id] = 2

    new_notification_invite(auth_user_id, u_id, channel_id, 'channels')
    data_store.set(store)
    return {}

def channel_details_v1(auth_user_id, channel_id):
    '''
    Given a channel with ID channel_id that the 
    authorised user is a member of, provide 
    basic details about the channel.

    Arguments:
        auth_user_id (int)
        channel_id (int)

    Exceptions:
        InputError: 
        - Occurs when channel_id does 
          not refer to a valid channel

        AccessError: 
        - Occurs when channel_id is 
          valid and the authorised user
          is not a member of the channel

    Return Value:
        Returns channel['name']
        Returns channel['is_public']
        Returns channel['owner_members']
        Returns channel['all_members']

    '''  

    store = data_store.get()
    
    valid_channel = store['channels'].get(channel_id)
    if valid_channel == None: 
        raise InputError("Invalid channel id")

    if auth_user_id in valid_channel['members_id']:
        return {'name': valid_channel['name'],
                'is_public': valid_channel['is_public'],
                'owner_members': list(valid_channel['owner_members'].values()),
                'all_members': list(valid_channel['all_members'].values())}
    else:
        raise AccessError(description=\
            "User is not member of channel")

def channel_join_v1(auth_user_id, channel_id):
    '''
    Given a user_id and channel_id, 
    makes that user a member of 
    that channel if possible.

    Arguments:
        auth_user_id (int)
        channel_id (int)

    Exceptions:
        InputError 
            - channel_id is not a valid channel.
            - user is already a member of channel.

        AccessError - Occurs when:
            - user is not registered
            - user is trying to join private 
              channel and does not have global 
              owner permissions.

    Return Value:
        Returns {}

    '''     
    store = data_store.get()
    match_channel = store['channels'].get(channel_id)
    if match_channel == None:
        raise InputError(description=
            "Channel_id does not refer to a valid channel.")

    if auth_user_id in match_channel['members_id']:
        raise InputError(description=
            "The authorised user is already a member of the channel.")

    auth_user = find_user(auth_user_id)
    if match_channel['is_public'] == False and auth_user['permissions'] == 2:
        raise AccessError(description=
            "The channel_id refers to a private channel and\
             the authorised user lacks global permissions.")

    match_channel['members_id'].append(auth_user_id)
    match_channel['all_members'][auth_user_id] = condense_user(auth_user)
    auth_user['channels'][channel_id] = 2

    return {}

def channel_leave(auth_id, channel_id):
    '''
    Given an auth_id and a channel_id, 
    remove them as a member of the channel

    Arguments:
        auth_user_id (int)
        channel_id (int)

    Exceptions:
        InputError  - Occurs when:
            - Channel_id does not refer to a valid channel 
        AccessError - Occurs when:
            - Channel_id is valid and the authorised user 
              is not a member of the channel

    Return Value:
        Returns {}

    '''     

    store = data_store.get()
    channels = store['channels']
    valid_channel = channels.get(channel_id)

    if valid_channel == None: 
        raise InputError(description=
            "Channel_id does not refer to a valid channel.")

    user = find_user(auth_id)
    channel_role = user['channels'].get(channel_id)
    if channel_role == None:
        raise AccessError(description=
            "Channel_id is valid and the authorised user is not a member of the channel")

    valid_channel['all_members'].pop(auth_id)
    valid_channel['members_id'].remove(auth_id)

    if channel_role == 1:
        valid_channel['owner_members'].pop(auth_id)
        valid_channel['owner_id'].remove(auth_id)

    user['channels'].pop(channel_id)

    return {}

# auth_id : Person who calls the funtion 
# user_id: Is person being removed. 
def remove_owner(auth_user_id, channel_id, u_id): 
    '''
    Given an auth_id and a channel_id, 
    remove them as an owner of the channel

    Arguments:
        auth_user_id (int)
        channel_id (int)
        user_id (int)

    Exceptions:
        InputError  - Occurs when:
            - channel_id does not refer to a valid channel 
            - u_id does not refer to a valid user 
            - u_id refers to a user who is not a owner of the channel 
            - u_id refer to a user who is currently 
              the ownly owner of the channel 

        AccessError - Occurs when:
            - Channel_id is valid and the authorised user
              does not have owner permissions in the channel

    Return Value:
        Returns {}

    '''         

    # check if channel_id is a valid channel
    store = data_store.get()

    valid_channel = store['channels'].get(channel_id)
    if valid_channel == None:
        raise InputError(description=
            "Channel_id does not refer to a valid channel")

    auth_user = find_user(auth_user_id)
    auth_channel_role = auth_user['channels'].get(channel_id)

    if auth_channel_role == None:
        raise AccessError(description=
            "auth_user_id is not a member of the channel")

    # check if the authorised id has owner permission or not
    if check_permissions(auth_user_id) != 1 and auth_channel_role == 2:
        raise AccessError(description=
            "The auth_user_id does not have owner permissions")

    # check if u_id is a valid user
    valid_user = find_user(u_id)
    if valid_user == None:
        raise InputError(description = 
            "u_id does not refer to a valid user")

    #Check is u_id is member of channel
    if valid_user['channels'].get(channel_id) == None:
        raise InputError(description=
            "u_id is not a member of the channel")

    #Check is u_id is owner of channel
    if valid_user['channels'].get(channel_id) == 2:
        raise InputError(description=
            "u_id is not an owner of the channel")

    # check if user id is the only owner 
    if len(valid_channel['owner_members']) == \
        1 and u_id in valid_channel['owner_id']: 

        raise InputError(description=
            "u_id refers to a user who is currently the only owner of the channel")

    valid_channel['owner_members'].pop(u_id)

    # change from owner to member
    valid_user['channels'][channel_id] = 2
    data_store.set(store)

    # Removing owner from owner_id list 
    valid_channel['owner_id'].remove(u_id)

    return {}

def channel_addowner_v1(auth_user_id, channel_id, u_id):
    """ 
    Make user with user id u_id an owner of the channel.
    
    Arguments:
        auth_user_id (int)
        channel_id (int)
        u_id (int)

    Exceptions:
        Input Error:
            - channel_id does not refer to a valid channel
            - u_id does not refer to a valid user
            - u_id refers to a user who is not 
              a member of the channel
            - u_id refers to a user who is already 
              an owner of the channel

    Access Error:
        - channel_id is valid and the authorised
          user does not have owner permission 
          in the channel

    Return Type:
        {} 
    """
    # check if channel_id is a valid channel
    store = data_store.get()
    valid_channel = store['channels'].get(channel_id)
    if valid_channel == None:
        raise InputError(description=
            "Channel_id does not refer to a valid channel.")

    # check if u_id is a valid user
    valid_user = find_user(u_id)
    if valid_user == None:
        raise InputError(description = "u_id is not valid.")

    auth_user = find_user(auth_user_id)
    auth_channel_role = auth_user['channels'].get(channel_id)

    # check if auth_user_id is a member of the channel
    if auth_channel_role == None:
        raise AccessError(description=
            "auth_user_id is not a member of the channel")

    # check if the authorised id has owner permissions or is a owner of the channel
    if check_permissions(auth_user_id) != 1 and auth_channel_role == 2:
        raise AccessError(description=
            "The auth_user_id does not have owner permissions")

    user_channel_role = valid_user['channels'].get(channel_id)
    if user_channel_role == None:
        raise InputError(description="u_id is not a member of the channel")

    if user_channel_role == 1:
            raise InputError(description="u_id is already a owner")

    valid_channel['owner_members'][u_id] = condense_user(valid_user)
    valid_channel['owner_id'].append(u_id)

    # change from member to owner in users
    valid_user['channels'][channel_id] = 1
    data_store.set(store)
    return {}

