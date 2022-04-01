
import hashlib
import jwt
import random
import smtplib
import os
from src.data_store import data_store
from src.error import InputError, AccessError
from src.helpers import find_user, add_user_stats, email_validity


SECRET = 'dromedarycamel'
EMAIL_ADDRESS = 'camelstreams@gmail.com'
EMAIL_PASSWORD = 'Aykjhfdk445'
Constant = 2

def decode_jwt(token):
    return jwt.decode(token, SECRET, algorithms='HS256')

def auth_login_v1(email, password):
    """
    Given a registered user's email and password, 
    returns their `auth_user_id` value.
    
    Arguments:
        email(string)
        password(string)
    
    Exceptions:
        Inputerror:
            email entered does not belong to a user.
            password is not correct.
            
    Return Type:
        {auth_user_id} when password fits the valid email.

    """
    store = data_store.get()
    users = store['users']
    for user in users:
        #check if email has been registered
        if user['email'] == email: 
            #check if password match the email
            if user['password'] == hashlib.sha256(password.encode()).hexdigest(): 
                store['active_sessions'][store['session_num'] + 1] = user['u_id']
                store['session_num'] += 1
                return {
                    'auth_user_id' : user.get('u_id')
            }
            else: 
                raise InputError(description = 'password_not_matching')

    raise InputError(description="Email not in use.")



def check_dupe(handle, num):
    '''
    - Checks if a created handle already is in use. 
    - If so, recursively calls itself, incrementing 
    an integer that is appended to the created handle 
    until a unique handle has been made, with the 
    lowest possible appended value. 
    - num represents the integer being appended, 
    with -1 representing a unique handle.

    Arguments:
        handle (string)
        num (int)

    Return Value:
        Returns new_handle (string)

    '''
    store = data_store.get()

    new_handle = handle if num == -1 else handle + str(num)
    
    if new_handle in store['handles']:
        new_handle = check_dupe(handle, num + 1)
    
    return new_handle

def handle_gen(name_first, name_last):
    '''
    Given a first name and last name, returns a unique 
    handle. The handle is created by taking the first 
    20 non-alphanumeric characters in the concatenated
    first and last name and making any uppercase 
    characters lowercase. If this handle is already 
    in use, the smallest integer possible that would 
    result in a unique handle is appended.

    Arguments:
        name_first (string)
        name_last (string)

    Return Value:
        Returns handle_str (string)

    '''

    handle = ''

    for i in name_first + name_last:
        if i.isalpha() or i.isnumeric():
            handle += i

    if len(handle) == 0:
        raise InputError(description='Cannot have empty handle.')

    if len(handle) > 20:
        handle = handle[:20]

    handle = handle.lower()

    handle = check_dupe(handle, -1)

    return handle

def auth_register_v1(email, password, name_first, name_last):
    '''
    Given a first name, last name, email address and password,
    creates a new account with these details, creates an unused handle
    to be associated with this account, and returns a new auth_user_id.

    Arguments:
        email (string)
        password (string)
        name_first (string)
        name_last (string)

    Exceptions:
        InputError  - Occurs when:
            Email address is not in a valid format.
            Email address is already associated with another account.
            Length of password is less than 6 characters.
            Length of name_first is not between 1 and 50 characters inclusive.
            Length of name_last is not between 1 and 50 characters inclusive.
            name_first and name_last solely consist of non-alphanumeric characters.

    Return Value:
        Returns {auth_user_id} on successful account creation.

    '''

    if email_validity(email) == None:
        raise InputError(description=
            "The email entered is not a valid email.")
    
    if len(password) < 6:
        raise InputError(description=
            "Length of password is less than 6 characters.")

    if len(name_first) < 1 or len(name_first) > 50:
        raise InputError(description=
            "Length of name_first is not between 1 and 50 characters inclusive")

    if len(name_last) < 1 or len(name_last) > 50:
        raise InputError(description=
            "Length of name_last is not between 1 and 50 characters inclusive")

    store = data_store.get()

    for user in store['users']:
        if user['email'] == email:
            raise InputError(description=
                "Email address is already being used by another user.")

    user = {'u_id': len(store['users']) + len(store['removed_users']) + 1,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'name_first': name_first,
            'name_last': name_last, 
            'handle_str': handle_gen(name_first, name_last)
            }


    #Global permissions, where 1 is admin and 2 is normal user
    user['permissions'] = 1 if store['admin_num'] == 0 else 2

    if store['admin_num'] == 0:
        store['admin_num'] += 1
    
    #Dictionary, where key is dm_id and value is 1 if owner, 2 if member
    user['dms'] = {}

    #Dictionary, where key is channel_id and value is 1 if owner, 2 if member
    user['channels'] = {}

    #Set containing all message_ids of messages sent by user
    user['sent_messages'] = set()

    #for the user stats
    user['time_stamped'] = {
        'channel': 0,
        'message': 0,
        'dm': 0
    }
    
    user['channels_joined'] = 0
    user['dms_joined'] = 0
    user['messages_sent'] = 0
    user['channel_dict'] = []
    user['dm_dict'] = []
    user['message_dict'] = []
    
    


    #List of notification dictionaries
    user['notifications'] = []


    #Dictionary where each key is a session id with corresponding user_id
    store['active_sessions'][store['session_num'] + 1] = user['u_id']

    store['session_num'] += 1
    store['handles'][user['handle_str']] = user['u_id']

    store['users'].append(user)
    
    data_store.set(store)
    add_user_stats(user['u_id'])

    return {
        'auth_user_id' : user.get('u_id')
    }

def auth_logout_v1(token):
    '''
    Given an active token, invalidates the token to log the user out.

    Argument:
        token
    
    '''
    try:
        target = decode_jwt(token)
        store = data_store.get()
        match_user = store['active_sessions'].get(target['session_id'])
        if match_user == target['auth_user_id'] :
            store['active_sessions'].pop(target['session_id'])
        else:
            raise AccessError(description = "Invalid token.")
    except Exception as e:
        raise AccessError(description = "Invalid token.") from e

    return {}

def auth_passwordreset_request(email):
    '''
    Given an email address, if the user is a registered user, sends them an 
    email containing a specific secret code, that when entered in 
    auth/passwordreset/reset, shows that the user trying to reset the 
    password is the one who got sent this email. 
    
    Argument:
        email (string)

    Return Value:
        {}

    '''
    # check if email is registered to a valid user
    valid_user = None
    store = data_store.get()
    for user in store['users']:
        if email == user['email']:
            valid_user = user
    
    if valid_user == None:
        # A email is not sent when the email is not a valid user
        return {}

    # Make sure user is logged out of all sessions
    active_session = store['active_sessions']
    to_remove = []
    for session in active_session:
        if active_session[session] == valid_user['u_id']:
            to_remove.append(session)

    # removing sessions from active sessions
    for remove in to_remove:
        active_session.pop(remove)

    # Generate a unique 6 digit Secret code
    code_data = store['pass_reset_codes']
    secret_code = 100000 + len(code_data) + Constant

    # save secret code in the data_store with the user id
    code_data[secret_code] = valid_user['u_id']

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        subject = "UNSW STREAMS: Password Reset"
        body = \
            f"Hi {valid_user['name_first']},\nWe received a request \
            to reset the password for your account.\nYour rest code is {secret_code}"

        msg = f"Subject: {subject}\n\n{body}"        
        smtp.sendmail(EMAIL_ADDRESS, email, msg)

    data_store.set(store)
    return {}

def auth_passwordreset_reset(reset_code, new_password):
    '''
    Given a reset code for a user, set that 
    user's new password to the password provided.
    
    Arguments:
        reset_code (str)
        new_password (str)

    Exception:
        Input Error:
            - reset_code is not a valid reset code
            - password entered is less than 6 characters long

    Return Type:
    {}
    '''
    store = data_store.get()
    # check reset code
    reset_code = int(reset_code)
    if reset_code not in store['pass_reset_codes'].keys():
        raise InputError(description = f"Invalid reset code: {reset_code}")

    # check  if new password is less than 6 characters
    if len(new_password) < 6:
        raise InputError(description = "Length of password is less than 6 characters.")

    # get user
    user_data = store['pass_reset_codes']
    user = find_user(user_data[reset_code])

    # change password
    user['password'] = hashlib.sha256(new_password.encode()).hexdigest()

    #delete reset code
    store['pass_reset_codes'].pop(reset_code)
    data_store.set(store)
    return {}
