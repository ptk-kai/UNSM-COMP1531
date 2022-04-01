from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user, name_length_test, find_remove_user, condense_user, email_validity
from src import config
from PIL import Image
import sys
import urllib.request
import requests

def user_profile_v1(u_id):
    """ 
    For a valid user, returns information about their
    user_id, email, first name, last name, and handle
    
    Arguments:
        u_id (int)

    Return Type:
        { user : { 
            u_id (int)
            email (string)
            name_first (string)
            name_last (string)
            handle (string)
            } 
        } 
    """
    # check if user is valid
    user = find_user(u_id)
    if user == None:
        user = find_remove_user(u_id)
        if user == None:
            raise InputError(description = "user_id is not a valid id")

    return {'user': condense_user(user)}

def user_profile_setname_v1(auth_user_id, first_name, last_name):
    """ 
    Update the authorised user's first and last name

    Input Error:
        - length of name_first is not between 1 and 50 characters inclusive
        - length of name_last is not between 1 and 50 characters inclusive

    Arguments:
        auth_user_id (int)
        first_name (string)
        last_name (string)

    Return Type:
        {} 
    """

    # check if auth_user_id is valid
    auth_user = find_user(auth_user_id)

    # Update first name in users data store
    if name_length_test(first_name) == False:
        raise InputError(description = 
            'first name is not between 1 and 50 characters')

    auth_user['name_first'] = first_name 

    # Update last name in users data store
    if name_length_test(last_name)  == False:
        raise InputError(description = 
            'Last name is not between 1 and 50 characters') 
    
    auth_user['name_last'] = last_name

    #Update names in channels
    store = data_store.get()
    
    for channel in auth_user['channels']:
        match = store['channels'].get(channel)
        match['all_members'][auth_user_id]['name_first'] = first_name
        match['all_members'][auth_user_id]['name_last'] = last_name

        if auth_user['channels'].get(channel) == 1:
            match['owner_members'][auth_user_id]['name_first'] = first_name
            match['owner_members'][auth_user_id]['name_last'] = last_name

    for dm in auth_user['dms']:
        match = store['dms'].get(dm)
        match['members'][auth_user_id]['name_first'] = first_name
        match['members'][auth_user_id]['name_last'] = last_name

                
    data_store.set(store)

    return {}

def user_profile_setemail_v1(auth_user_id, email):
    '''
    Update the authorised user's email address

    Input Error:
        1.email entered is not a valid email (more in section 6.4)
        2.email address is already being used by another user
    
    Argument:
        auth_user_id(int)
        email(string)
    
    Return Type:
        {}
    '''


    
    # Update email in users data store
    if email_validity(email) == None:
        raise InputError(description = 
            "The email entered is not a valid email.")
    
    store = data_store.get()
    
    is_in_use = False
    for user in store['users']:
        if user['email'] == email:
            is_in_use = True
            
    if is_in_use == True:
        raise InputError(description = 
            "Email address is already being used by another user.")
    
    auth_user = find_user(auth_user_id)
    auth_user['email'] = email
    
    #Update names in channels
    
    for channel in auth_user['channels']:
        match = store['channels'].get(channel)
        match['all_members'][auth_user_id]['email'] = email

        if auth_user['channels'].get(channel) == 1:
            match['owner_members'][auth_user_id]['email'] = email
  

    for dm in auth_user['dms']:
        match = store['dms'].get(dm)
        match['members'][auth_user_id]['email'] = email


    data_store.set(store)

    return {}

def user_profile_sethandle_v1(auth_user_id, handle_str):
    '''
    Update the authorised user's handle (i.e. display name)
    
    Input Error:
        1.length of handle_str is not between 3 and 20 characters inclusive
        2.handle_str contains characters that are not alphanumeric
        3.the handle is already used by another user
    Argument:
        auth_user_id(int)
        handle_str(string)
    
    Return Type:
        {}
    '''
  

    #update handle_str in users data store
    store = data_store.get() 
    
    for i in handle_str:
        if i.isalpha() == False and i.isnumeric() == False:
            raise InputError(description = 
                'handle_str contains characters that are not alphanumeric') 

    if  len(handle_str) < 3 or len(handle_str) > 20:
        raise InputError(description = 
            'length of handle_str is not between 3 and 20 characters inclusive')      
    
    for user in store['users']:
        if user['handle_str'] == handle_str:
            #If handle is in use, raise error
            raise InputError(description = 
                'the handle is already used by another user')
    

    #Update emailhandle in channels
    auth_user = find_user(auth_user_id)
    store['handles'].pop(auth_user['handle_str'])
    store['handles'][handle_str] = auth_user_id
    auth_user['handle_str'] = handle_str
    
    for channel in auth_user['channels']:
        match = store['channels'].get(channel)
        match['all_members'][auth_user_id]['handle_str'] = handle_str

        if auth_user['channels'].get(channel) == 1:
            match['owner_members'][auth_user_id]['handle_str'] = handle_str
  
    for dm in auth_user['dms']:
        match = store['dms'].get(dm)
        match['members'][auth_user_id]['handle_str'] = handle_str

    data_store.set(store)

    return {}
'''
def user_profile_uploadphoto_v1(auth_user_id, img_url, x_start, y_start, x_end, y_end):
    
    Given a URL of an image on the internet, 
    crops the image within bounds (x_start, y_start) and (x_end, y_end). 
    Position (0,0) is the top left. 
    Please note: the URL needs to be a non-https URL 
    (it should just have "http://" in the URL. We will only test with non-https URLs.)
    
    Input Error:
        1.img_url returns an HTTP status other than 200.
        2.any of x_start, y_start, x_end, y_end are not within the dimensions of the image at the URL.
        3.x_end is less than x_start or y_end is less than y_start.
        4.image uploaded is not a JPG.
    
    Argument: 
        1.auth_user_id(int)
        2.img_url(string)
        3.x_start(int)
        4.y_start(int)
        5.x_end(int)
        6.y_end(int)
        
    Return Type:
        {}
        raise 
    
    r = requests.get(img_url)
    if r.status_code != 200:
        raise InputError(description = 'img_url returns an HTTP status other than 200.')
    
    if img_url[-3:] != 'jpg' and img_url[-4:] != 'jpeg':
        raise InputError(description = 'image uploaded is not a JPG.')
    
    
    if int(x_end) < int(x_start) or int(y_end) < int(y_start):
        raise InputError(description = 'x_end is less than x_start or y_end is less than y_start.')
    
    name = f"src/static/{auth_user_id}.jpg"
    urllib.request.urlretrieve(img_url, name)
    img = Image.open(name)
    width, height = img.size
    if int(x_start) < 0 or int(y_start) < 0 or int(x_end) > width or int(y_end) > height:
        raise InputError(description = 'any of x_start, y_start, x_end, y_end are not within the dimensions of the image at the URL.')
    cropped = img.crop((int(x_start), int(y_start), int(x_end), int(y_end)))
    cropped.save(name)
    
    user = find_user(auth_user_id)
    user['profile_img_url'] = name
    
    return {}
'''
def user_stats_v1(auth_user_id):
    '''
    Fetches the required statistics about this user's use of UNSW Streams.
    
    Argument:
        1.auth_user_id(int)
    
    Return type:
        {
        'channels_joined':[{num_channels_joined(int), time_stamp(int)}],
        'dms_joined': [{num_dms_joined(int), time_stamp(int)}],
        'message_sent': [{num_messages_sent (int), time_stamp(int)}],
        'involvement_rate'
    '''
   
    store = data_store.get()
    
    user = find_user(auth_user_id)
            
    nume = len(user['dms']) + len(user['channels']) + len(user['sent_messages'])
    deno = store['channel_num'] + store['message_num'] + store['dm_num']
    if deno == 0:
        rate = 0
    else:
        rate = float(nume / deno)
        if rate > 1:
            rate = 1
    
    
    return {
        'user_stats':{
            'channels_joined': user['channel_dict'],
            'dms_joined': user['dm_dict'],
            'messages_sent': user['message_dict'],
            'involvement_rate': rate
        }
    }