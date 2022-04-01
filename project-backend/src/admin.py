from src.helpers import find_user
from src.message import message_edit
from src.error import AccessError, InputError
from src.user import user_profile_setname_v1
from src.data_store import data_store
from src.dm import dm_leave_v1
from src.helpers import condense_user
from src.channel import channel_leave

def admin_remove_user(auth_user_id, u_id):
    '''
    - Given a user by their u_id, remove them from the Streams. 
    - They are removed from all channels/DMs, and will not be 
    included in the list of users returned by users/all.
    - Streams owners can remove other Streams owners 
    (including the original first owner).
    - Once users are removed, the contents of the messages 
    they sent will be replaced by 'Removed user'. 
    - Their profile is still retrievable with user/profile, 
    however name_first is'Removed' and name_last is 'user'. 
    - The user's email and handle is reusable.

    Arguments:
        auth_user_id (int)
        u_id (int)

    Exceptions:
        InputError  - Occurs when:
            u_id does not refer to a valid user
            u_id refers to a user who is the only global owner

        AccessError - Occurs when:
            the auth_user_id does not refer to a global owner

    '''

    store = data_store.get()
    auth_user = find_user(auth_user_id)

    if auth_user['permissions'] == 2:
        raise AccessError(description= \
            'User does not have global permissions.')

    if auth_user_id == u_id and store['admin_num'] == 1:
        raise InputError(description=\
            'Global user cannot remove themselves\
             if they are the only global owner')

    removed_user = find_user(u_id)

    if removed_user == None:
        raise InputError(description=\
            'u_id does not refer to a valid user.')

    for message in removed_user['sent_messages']:
        message_edit(u_id, message, 'Removed user')

    for channel in list(removed_user['channels']):
        channel_leave(u_id, channel)

    for dm in list(removed_user['dms']):
        dm_leave_v1(u_id, dm)

    user_profile_setname_v1(u_id, 'Removed', 'user')

    active_sessions = []
    for session in store['active_sessions']:
        if store['active_sessions'][session] == u_id:
            active_sessions.append(session)

    for session in active_sessions:
        store['active_sessions'].pop(session)

    store['users'].remove(removed_user)
    store['removed_users'].append(removed_user)

    data_store.set(store)

def admin_change_user_permissions(auth_user_id, u_id, permission_id):
    '''
    Given a user by their user ID, set their permissions 
    to new permissions described by permission_id.

    Arguments:
        - auth_user_id (int)
        - u_id (int)
        - permission_id (int)

    Exceptions:
        InputError  - Occurs when:
            - u_id does not refer to a valid user
            - u_id refers to a user who is the only global 
              owner and they are being demoted to member
            - permission_id is invalid

        AccessError - Occurs when:
            - the auth_user_id does not refer to a global owner

    '''

    auth_user = find_user(auth_user_id)

    if auth_user['permissions'] != 1:
        raise AccessError(\
            description="Only global users can change permissions.")

    user = find_user(u_id)
    if user == None:
        raise InputError(description="Invalid user")

    store = data_store.get()

    if user['permissions'] == permission_id:
        return

    if store['admin_num'] == 1 and auth_user_id == u_id:
        raise InputError(description=\
            "Cannot demote only global user.")

    if permission_id != 1 and permission_id != 2:
        raise InputError(description=\
            "Invalid permission id.")

    user['permissions'] = permission_id 

    if permission_id == 1:
        store['admin_num'] += 1
    else:
        store['admin_num'] -= 1

    data_store.set(store)