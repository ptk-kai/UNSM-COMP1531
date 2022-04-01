from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user, update_user_time_stamp, update_user_exists
from src.helpers import condense_user
from src.notification import new_notification_invite
from src.message import message_remove_v1


def dm_create_v1(auth_user_id, u_ids):
    '''
    - u_ids contains the user(s) that this DM is directed
    to, and does not include the creator. 
    - The creator is the owner of the DM. name is 
    automatically generated based on the users that
    are in this DM. 
    - The name is an alphabetically-sorted, 
    comma-and-space-separated list of user handles, 
    e.g. 'ahandle1, bhandle2, chandle3'.

    Arguments:
        auth_user_id (int)
        u_ids (list(int))

    Exceptions:
        InputError  - Occurs when:
            Any u_id in u_ids does not refer to a valid user.
            

    Return Value:
        Returns {dm_id}

    '''

    all_valid = True
    mem_list = {}
    hndl_list = []
    mem_ids = []

    store = data_store.get()
    dm_id = store['dm_num'] + 1 
    for user_id in u_ids:
        user = find_user(user_id)
        if user == None:
            all_valid = False
            break

    if all_valid == False:
        raise InputError(description="There is an invalid user in the list.")
    
    auth_user = find_user(auth_user_id)


    hndl_list.append(auth_user['handle_str'] + ", ")
    mem_list[auth_user_id] = condense_user(auth_user)
    mem_ids.append(auth_user_id)

    
    update_user_time_stamp('dm', auth_user_id)
    update_user_exists('dm', 'add', auth_user_id)
    for user_id in u_ids:
        user = find_user(user_id)
        user['dms'][dm_id] = 2
        mem_list[user_id] = condense_user(user)
        hndl_list.append(user['handle_str'] + ", ")
        mem_ids.append(user_id)
        update_user_time_stamp('dm', user_id)
        update_user_exists('dm', 'add', user_id)


    hndl_list.sort()
    name = ''

    for handle in hndl_list:
        name += handle
    name = name.strip(", ")

    store['dm_num'] += 1
    auth_user['dms'][dm_id] = 1
    
    new_dm = {
        'dm_id': dm_id,
        'name': name,
        'members' : mem_list,
        'messages': {},
        'owner_id':auth_user_id,
        'members_id': mem_ids
    }
    store['dms'][dm_id] = new_dm

    for user_id in u_ids:
        new_notification_invite(
            auth_user_id, user_id, dm_id, 'dms')

    data_store.set(store)

    return {
        'dm_id' : dm_id
    }

def dm_list_v1(auth_id):
    '''
    Input: token -> auth_id
    Returns the list of DMs that the user is a member of.
    '''
    dm_list = []
    store = data_store.get()
    for dm in store['dms']:
        if auth_id in store['dms'][dm]['members_id']:
            dm_list.append(
                {'dm_id': store['dms'][dm]['dm_id'],
                'name': store['dms'][dm]['name']})

    return {'dms': dm_list}   

def dm_details_v1(auth_user_id, dm_id):
    '''
    Given a DM with ID dm_id that the authorised user
    is a member of, provide basic details about the DM.

    Arguments:
        auth_id-int   
        dm_id-int   

    Exceptions:
        InputError:
            - Occurs when dm_id does not refer to a valid DM

        AccessError:
            - Occurs when dm_id is valid and the authorised
              user is not a member of the DM

    Return Value:
        Returns name
        Returns members
    '''

    store = data_store.get()
    dm = store['dms'].get(dm_id)

    if dm == None:
       raise InputError(description=
            "not valid dm id") 

    user = find_user(auth_user_id)
    if user['dms'].get(dm_id) == None:
        raise AccessError(description=
            "user is not a member of dm")
    
    return {
        'name': dm['name'], 
        'members': list(dm['members'].values())
         }

def dm_remove_v1(auth_user_id, dm_id):
    '''
    Remove an existing DM, so all members are no longer in the DM.
    This can only be done by the original creator of the DM.
    
    Arguments:
        auth_id-int   
        dm_id-int   

    Exceptions:
        InputError:
            - Occurs when dm_id does not refer to a valid DM

        AccessError:
             - Occurs when dm_id is valid and the authorised 
               user is not the original DM creator

    Return:
        {}
    '''
    store = data_store.get()

    match_dm = store['dms'].get(dm_id)
    if match_dm == None:
        raise InputError(description="not valid dm id")

    user = find_user(auth_user_id)
    dm_role =  user['dms'].get(dm_id)
    
    if dm_role == None:
        raise AccessError(description=
            "User is not a member of dm")

    if dm_role == 2:
        raise AccessError(description=
            "User is not creator of dm")

    message_list = list(match_dm['messages'])
    for message in message_list:
        message_remove_v1(auth_user_id, message)

    for user in match_dm['members']:
        match_user = find_user(user)
        match_user['dms'].pop(dm_id)
   
        update_user_time_stamp('dm', user)
        update_user_exists('dm', 'remove', user)    
    
    match_dm['members'].clear()
    match_dm['members_id'].clear()
    match_dm['owner_id'] = -1

    store['dms'].pop(dm_id)

    data_store.set(store)
    return {}

def dm_leave_v1(auth_user_id, dm_id):
    '''
    - Given a DM ID, the user is removed as a member of this DM.
    - The creator is allowed to leave and the DM will still 
      exist if this happens.
    - This does not update the name of the DM.

    Arguments:
        auth_id-int   
        dm_id-int   

    Exceptions:
        InputError: 
            - Occurs when dm_id does not refer to a valid DM
        AccessError:
            - Occurs when dm_id is valid and the authorised 
              user is not a member of the DM

    Return:
        {}
    '''
    store = data_store.get()
    match_dm = store['dms'].get(dm_id)

    if match_dm == None:
        raise InputError(description="not valid dm id")

    user = find_user(auth_user_id)
    dm_role = user['dms'].get(dm_id)

    if dm_role == None:
        raise AccessError(description=
            "user is not a member of dm")

    match_dm['members'].pop(auth_user_id)
    match_dm['members_id'].remove(auth_user_id)
    user['dms'].pop(dm_id)

    if dm_role == 1:
        match_dm['owner_id'] == None

    data_store.set(store)
    return {}
