from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user, condense_user, update_time_stamp

def users_all_v1():
    """ 
    Returns a list of all users and their associated details.
    
    Return Type:
        user (dictionary) 
    """

    user_list = []
    store = data_store.get()['users']
    for item in store:
        user_list.append(condense_user(item))

    return {"users": user_list}

def users_stats_v1():
    '''
    Fetches the required statistics about the use of UNSW Streams.

    Return Types:
        {
        'channels_exist': [{num_channels_exist (int), time_stamp (int)}],
        'dms_exist': [{num_dms_exist (int), time_stamp(int)}],
        'messages_exist' : [{num_messages_exist (int), time_stamp(int)}],
        'utilization_rate' (int) 
        }
    '''
    store = data_store.get()
    # get the utilization rate
    num_user = len(store['users'])
    joined_channel_dms = 0
    for user in store['users']:
        if len(user['channels']) > 0 or len(user['dms']) > 0:
            joined_channel_dms += 1
    
    rate = float(joined_channel_dms/num_user)

    # This is a template of the return value
    return { 
        'workspace_stats':{
            'channels_exist': store['channels_dict'],
            'dms_exist': store['dms_dict'],
            'messages_exist' : store['messages_dict'],
            'utilization_rate': rate,
        }
    }
