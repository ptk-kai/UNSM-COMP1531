import sys
import signal
import pickle

import requests
import jwt

from json import dumps
from flask import Flask, request, send_from_directory
from flask.wrappers import Request
from flask_cors import CORS
from src.error import InputError, AccessError
from src import config
import time

from src.other import clear_v1, search_v1
from src.auth import auth_login_v1, auth_logout_v1, auth_register_v1, auth_passwordreset_request, auth_passwordreset_reset
from src.data_store import data_store
from src.channels import channels_create_v1, channels_listall_v1, channels_list_v1
from src.channel import channel_invite_v1, channel_details_v1, channel_join_v1, channel_leave, remove_owner, channel_addowner_v1
from src.dm import dm_leave_v1, dm_create_v1, dm_list_v1, dm_details_v1, dm_remove_v1
from src.message import message_pin_v1, message_unpin_v1

from src.message import message_send, message_get_v1, message_remove_v1, message_edit, message_react_v1, message_unreact_v1, send_message_later, message_share
from src.helpers import find_user, update_exists, update_time_stamp, add_stats, add_user_stats, update_user_time_stamp, update_user_exists, update_data_p, update_data_store

from src.users import users_all_v1, users_stats_v1
from src.user import user_profile_v1, user_profile_setname_v1, user_profile_setemail_v1, user_profile_sethandle_v1, user_stats_v1
from src.admin import admin_remove_user, admin_change_user_permissions
from src.standup import is_standup_active, start_standup, send_message_standup
from src.notification import get_notifications


SECRET = 'dromedarycamel'

def create_jwt(auth_user_id, session_id):
    '''
    Returns a jwt token containing auth_id and session_id.

    '''
    return jwt.encode({'auth_user_id': auth_user_id, 'session_id': session_id}, SECRET, algorithm='HS256')

def decode_jwt(token):
    '''
    Returns the contents of a jwt token.

    '''
    return jwt.decode(token, SECRET, algorithms='HS256')

def token_auth_id(token):
    '''
    Takes in a user token and returns the auth_user_id if the session is valid.

    '''
    try:
        store = data_store.get()
        decoded = jwt.decode(token, SECRET, algorithms='HS256')
        if (decoded['session_id'] in store['active_sessions'] and \
            store['active_sessions'][decoded['session_id']] == decoded['auth_user_id']):

            decoded = decoded['auth_user_id']

        else:
            raise AccessError(description="Invalid token.")
    except Exception as e:
        raise AccessError(description="Invalid token.") from e

    return decoded

#Decorator function
def start_request(function):
    '''
    This is a function decorator for any route but the GET route.
    It takes in the function that will be wrapped.
    
    ''' 
    def wrapped():
        update_data_store()
        request_data = request.get_json()
        return function(request_data)
    return wrapped

def start_arguments(function):
    '''
    This function decorator is for the GET routes
    '''
    def wrapper(*args):
        update_data_store()
        token = request.args.get('token')
        auth_id = token_auth_id(token)
        return function(auth_id)
    return wrapper

def start_messages(function):
    '''
    This function decorator is for GET messages functions
    '''
    def wrapper(*args):
        start = request.args.get('start', type = int)
        return function(args[0], start)
    return wrapper

def quit_gracefully(*args):
    '''For coverage'''
    exit(0)

def defaultHandler(err):
    response = err.get_response()
    print('response', err, err.get_response())
    response.data = dumps({
        "code": err.code,
        "name": "System Error",
        "message": err.get_description(),
    })
    response.content_type = 'application/json'
    return response

APP = Flask(__name__, static_url_path='/src/static/')
CORS(APP)

APP.config['TRAP_HTTP_EXCEPTIONS'] = True
APP.register_error_handler(Exception, defaultHandler)

#### NO NEED TO MODIFY ABOVE THIS POINT, EXCEPT IMPORT
###############################################################################

@APP.route("/echo", methods=['GET'])
def echo():
    data = request.args.get('data')
    if data == 'echo':
   	    raise InputError(description='Cannot echo "echo"')
    return dumps({
        'data': data
    })

@APP.route("/clear/v1", methods = ['DELETE'])
def clear():
    clear_v1()
    update_data_p()
    return dumps({})

@APP.route("/auth/register/v2", methods = ['POST'], endpoint = 'register')
@start_request
def register(request_data):
    add_stats()
    ret = auth_register_v1(\
        request_data['email'], 
        request_data['password'], 
        request_data['name_first'], 
        request_data['name_last'])

    update_data_p()
    store = data_store.get()
    return dumps({
        'token'        : create_jwt(ret['auth_user_id'], store['session_num']), 
        'auth_user_id' : ret['auth_user_id']
        })

@APP.route("/auth/login/v2", methods = ['POST'], endpoint = 'login')
@start_request
def login(request_data):
    ret = auth_login_v1(\
        request_data['email'], 
        request_data['password'])
        
    update_data_p()
    store = data_store.get()
    return dumps({
        'token'        : create_jwt(ret['auth_user_id'], store['session_num']), 
        'auth_user_id' : ret['auth_user_id']
        })

@APP.route("/auth/logout/v1", methods = ['POST'], endpoint = 'logout')
@start_request
def logout(request_data):
    output = auth_logout_v1(request_data['token'])
    update_data_p()
    return dumps(output)

@APP.route("/channels/create/v2", methods = ['POST'], endpoint = 'channels_create')
@start_request
def channels_create(request_data):
    output = channels_create_v1(\
        token_auth_id(request_data['token']), 
        request_data['name'], 
        request_data['is_public'])
    update_time_stamp('channel')
    update_user_time_stamp('channel', token_auth_id(request_data['token']))
    update_exists('channel','add')

    update_user_exists('channel','add', token_auth_id(request_data['token']))
    update_data_p()
    return dumps(output)

@APP.route("/channel/join/v2", methods = ['POST'], endpoint = 'join_channel')
@start_request
def join_channel(request_data):
    
    
    output = channel_join_v1(token_auth_id(request_data['token']), request_data['channel_id'])
    update_user_time_stamp('channel', token_auth_id(request_data['token']))
    update_user_exists('channel','add', token_auth_id(request_data['token']))
    update_data_p()
    return dumps(output)

@APP.route("/channel/invite/v2", methods = ['POST'], endpoint = 'invite')
@start_request
def invite(request_data):

    output = channel_invite_v1(token_auth_id(request_data['token']),request_data['channel_id'], request_data['u_id'])
    update_user_time_stamp('channel', token_auth_id(request_data['token']))
    update_user_exists('channel','add', token_auth_id(request_data['token']))

    update_data_p()
    return dumps(output)

@APP.route("/message/send/v1", methods = ['POST'], endpoint = 'send_message_channel')
@start_request
def send_message_channel(request_data):
    auth_id = token_auth_id(request_data['token'])

    ret = message_send(\
        auth_id, 
        request_data['channel_id'], 
        request_data['message'], 
        'channels', 
        None, 
        False)

    update_data_p()
    return dumps({'message_id' : ret['message_id']})

@APP.route("/channel/messages/v2", methods = ['GET'], endpoint = 'load_messages_channel')
@start_arguments
@start_messages
def load_messages_channel(auth_id, start):
    channel_id = request.args.get('channel_id', type = int)
    ret = message_get_v1(auth_id, channel_id, start, 'channels')

    update_data_p()
    return dumps({
        'messages': ret['messages'],
        'start' : start,
        'end' : ret['end']
    })

@APP.route("/dm/create/v1", methods = ['POST'], endpoint = 'create_dm')
@start_request
def create_dm(request_data):
    auth_id = token_auth_id(request_data['token'])
    ret = dm_create_v1(auth_id, request_data['u_ids'])
    update_time_stamp('dm')
    
    update_exists('dm','add')
    
    update_data_p()
    return dumps({
        'dm_id' : ret['dm_id']
    })


@APP.route("/message/senddm/v1", methods = ['POST'], endpoint = 'send_message_dm')
@start_request
def send_message_dm(request_data):
    auth_id = token_auth_id(request_data['token'])

    ret = message_send(\
        auth_id, 
        request_data['dm_id'], 
        request_data['message'], 
        'dms', 
        None, 
        False)

    update_data_p()
    return dumps({'message_id' : ret['message_id']})

@APP.route("/dm/messages/v1", methods = ['GET'], endpoint = 'load_messages_dm')
@start_arguments
@start_messages
def load_messages_dm(auth_id,start):
    dm_id = request.args.get('dm_id', type = int)
    ret = message_get_v1(auth_id, dm_id, start, "dms")

    update_data_p()
    return dumps({
        'messages': ret['messages'],
        'start' : start,
        'end' : ret['end']
    })

@APP.route("/channels/listall/v2", methods=['GET'], endpoint = 'list_all_channels')
@start_arguments
def list_all_channels(auth_id):
    update_data_p()
    return dumps(channels_listall_v1())

@APP.route("/dm/list/v1", methods=['GET'], endpoint = 'dm_list_v1_route')
@start_arguments
def dm_list_v1_route(auth_id):
    update_data_p()
    return dumps(dm_list_v1(auth_id))

@APP.route("/users/all/v1", methods=['GET'], endpoint = 'list_users')
@start_arguments
def list_users(auth_id):
    output = users_all_v1()

    update_data_p()
    return dumps(output)

@APP.route("/user/profile/v1", methods=['GET'], endpoint = 'return_user_profile')
@start_arguments
def return_user_profile(auth_id):
    u_id = request.args.get('u_id', type = int)
    output = user_profile_v1(u_id)

    update_data_p()
    return dumps(output)

@APP.route("/user/profile/setname/v1", methods=['PUT'], endpoint = 'update_name')
@start_request
def update_name(request_data):
    output = user_profile_setname_v1(\
    token_auth_id(\
        request_data['token']), 
        request_data['name_first'],
        request_data['name_last'])

    update_data_p()
    return dumps(output)

@APP.route("/user/profile/setemail/v1", methods=['PUT'], endpoint = 'update_email')
@start_request
def update_email(request_data):
    output = user_profile_setemail_v1(\
        token_auth_id(request_data['token']), 
        request_data['email'])

    update_data_p()
    return dumps(output)

@APP.route("/user/profile/sethandle/v1", methods=['PUT'], endpoint = 'update_handle')
@start_request
def update_handle(request_data):
    output = user_profile_sethandle_v1(\
        token_auth_id(request_data['token']), 
        request_data['handle_str'])

    update_data_p()
    return dumps(output)

@APP.route("/dm/details/v1", methods=['GET'], endpoint = 'details_of_dm_v1')
@start_arguments
def details_of_dm_v1(auth_user_id):
    dm_id = request.args.get('dm_id', type=int)
    update_data_p()
    return dumps(dm_details_v1(auth_user_id, dm_id))


@APP.route("/dm/remove/v1", methods=['DELETE'], endpoint = 'remove_dm_v1')
@start_request
def remove_dm_v1(payload):

    token = payload['token']
    auth_user_id = token_auth_id(token)
    dm_id = payload['dm_id']
    dm_remove_v1(auth_user_id, dm_id)
    update_time_stamp('dm')    
    update_exists('dm','remove')
    

    update_data_p()
    return dumps({})

@APP.route('/channels/list/v2', methods=['GET'], endpoint = 'channels_list')
@start_arguments
def channels_list(auth_id):
    output = channels_list_v1(auth_id)

    update_data_p()
    return dumps(output)

@APP.route('/channel/details/v2', methods=['GET'], endpoint = 'details')
@start_arguments
def details(auth_id):
    channel_id = request.args.get('channel_id', type=int)
    output = channel_details_v1( auth_id, channel_id)

    update_data_p()
    return dumps(output)

@APP.route('/channel/leave/v1', methods=['POST'], endpoint = 'leave')
@start_request
def leave(request_data):
    channel_leave(
        token_auth_id(request_data['token']), 
        request_data['channel_id'])
    update_user_time_stamp('channel', token_auth_id(request_data['token']))
    update_user_exists('channel', 'remove', token_auth_id(request_data['token']))
    update_data_p()
    return dumps({})

@APP.route('/channel/removeowner/v1', methods=['POST'], endpoint = 'rm_owner')
@start_request
def rm_owner(request_data):
    remove_owner(
        token_auth_id(request_data['token']), 
        request_data['channel_id'], 
        request_data['u_id'])

    update_data_p()
    return dumps({})

@APP.route("/dm/leave/v1", methods=['POST'], endpoint = 'leave_the_dm')
@start_request
def leave_the_dm(payload):
    token = payload['token']
    auth_user_id = token_auth_id(token)
    dm_id = payload['dm_id']
    dm_leave_v1(auth_user_id, dm_id)

    update_user_time_stamp('dm', auth_user_id)
    update_user_exists('dm','remove', auth_user_id)

    update_data_p()
    return dumps({})

@APP.route("/message/sendlater/v1", methods=['POST'], endpoint = 'send_later_channel')
@start_request
def send_later_channel(request_data):
    resp = send_message_later(\
        token_auth_id(request_data['token']), 
        request_data['channel_id'], 
        request_data['message'], 
        'channels', 
        request_data['time_sent'])

    update_data_p()
    return dumps(resp)

@APP.route("/message/sendlaterdm/v1", methods=['POST'], endpoint = 'send_later_dm')
@start_request
def send_later_dm(request_data):
    resp = send_message_later(\
        token_auth_id(request_data['token']), 
        request_data['dm_id'], 
        request_data['message'], 
        'dms', 
        request_data['time_sent'])

    update_data_p()
    return dumps(resp)
 
@APP.route("/standup/start/v1", methods=['POST'], endpoint = 'standup_start')
@start_request
def standup_start(request_data):
    resp = start_standup(\
        token_auth_id(request_data['token']), 
        request_data['channel_id'], 
        request_data['length'])

    update_data_p()
    return dumps(resp)
    
@APP.route("/standup/send/v1", methods=['POST'], endpoint = 'standup_send')
@start_request
def standup_send(request_data):
    resp = send_message_standup(\
        token_auth_id(request_data['token']), 
        request_data['channel_id'], 
        request_data['message'])

    update_data_p()
    return dumps(resp)   

@APP.route('/standup/active/v1', methods=['GET'], endpoint = 'standup_active')
@start_arguments
def standup_active(auth_id):
    channel_id = request.args.get('channel_id', type = int)
    resp = is_standup_active(auth_id, channel_id)

    update_data_p()
    return dumps(resp)

@APP.route("/message/edit/v1", methods=['PUT'], endpoint = 'edit_message')
@start_request
def edit_message(request_data):
    message_edit(\
        token_auth_id(request_data['token']), 
        request_data['message_id'], 
        request_data['message'])

    update_data_p()
    return dumps({})

@APP.route("/admin/user/remove/v1", methods=['DELETE'], endpoint = 'remove_user_from_streams')
@start_request
def remove_user_from_streams(request_data):
    admin_remove_user(\
        token_auth_id(request_data['token']), 
        request_data['u_id'])

    update_data_p()
    return dumps({})

@APP.route("/message/remove/v1", methods=['DELETE'], endpoint = 'remove_message')
@start_request
def remove_message(request_data):
    message_remove_v1(\
        token_auth_id(request_data['token']), 
        request_data['message_id'])

    update_data_p()
    return dumps({})

@APP.route("/message/react/v1", methods=['POST'], endpoint = 'message_react')
@start_request
def message_react(request_data):
    message_react_v1(\
        token_auth_id(request_data['token']), 
        request_data['message_id'], 
        request_data['react_id'])

    update_data_p()
    return dumps({})

@APP.route("/message/unreact/v1", methods=['POST'], endpoint = 'message_unreact')
@start_request
def message_unreact(request_data):
    message_unreact_v1(\
        token_auth_id(request_data['token']),
        request_data['message_id'], 
        request_data['react_id'])

    update_data_p()
    return dumps({})

@APP.route("/message/share/v1", methods=['POST'], endpoint = 'message_share_v01')
@start_request
def message_share_v01(request_data):
    message_share(\
        token_auth_id(request_data['token']), 
        request_data['og_message_id'], 
        request_data['message'], 
        request_data['channel_id'],
        request_data['dm_id'])

    update_data_p()
    return dumps({})

@APP.route("/admin/userpermission/change/v1", methods=['POST'], endpoint = 'change_permissions')
@start_request
def change_permissions(request_data):
    admin_change_user_permissions(\
        token_auth_id(request_data['token']), 
        request_data['u_id'], 
        request_data['permission_id'])

    update_data_p()
    return dumps({})

@APP.route("/channel/addowner/v1", methods=['POST'], endpoint = 'add_owner')
@start_request
def add_owner(request_data):
    channel_addowner_v1(\
        token_auth_id(request_data['token']), 
        request_data['channel_id'], 
        request_data['u_id'])

    update_data_p()
    return dumps({})
    
@APP.route("/auth/passwordreset/request/v1", methods=['POST'], endpoint = 'request_password')
@start_request
def request_password(request_data):
    auth_passwordreset_request(request_data['email'])

    update_data_p()
    return dumps({})

@APP.route("/auth/passwordreset/reset/v1", methods = ["POST"], endpoint = 'reset_passwords')
@start_request
def reset_passwords(request_data):
    auth_passwordreset_reset(\
        request_data['reset_code'], 
        request_data['new_password'])

    update_data_p()
    return dumps({})

'''
@APP.route("/user/profile/uploadphoto/v1", methods = ["POST"], endpoint = 'uploadphoto')
@start_request
def uploadphoto(request_data):

    user_profile_uploadphoto_v1(token_auth_id(request_data['token']), request_data['img_url'], request_data['x_start'], request_data['y_start'], request_data['x_end'], request_data['y_end'])
    update_data_p()
    return dumps({})


@APP.route(f"/src/static/<path:path>")
def send_js(path):
    return send_from_directory('', path)
'''
@APP.route("/user/stats/v1", methods=['GET'], endpoint = 'user_stats')
@start_arguments
def user_stats(user_id):

    resp = user_stats_v1(user_id)
    update_data_p()
    return dumps(resp)
    

@APP.route("/notifications/get/v1", methods = ["GET"], endpoint = 'get_notification')
@start_arguments
def get_notification(auth_id):
    resp = get_notifications(auth_id)

    update_data_p()

    return dumps(resp)

@APP.route("/users/stats/v1", methods = ["GET"], endpoint = 'get_users_stats')
@start_arguments
def get_users_stats(auth_id):
    resp = users_stats_v1()

    update_data_p()
    return dumps(resp)
    
@APP.route("/message/pin/v1", methods=['POST'], endpoint = 'pin_message')
@start_request
def pin_message(request_data):
    message_pin_v1(\
        token_auth_id(request_data['token']), 
        request_data['message_id'])

    update_data_p()
    return dumps({})

@APP.route("/message/unpin/v1", methods=['POST'], endpoint = 'unpin_message')
@start_request
def unpin_message(request_data):
    message_unpin_v1(token_auth_id(\
        request_data['token']), 
        request_data['message_id'])

    update_data_p()
    return dumps({})
 
@APP.route('/search/v1', methods=['GET'], endpoint = 'search_message')
@start_arguments
def search_message(auth_id):
    query_str = request.args.get('query_str')
    output = search_v1(auth_id, query_str)

    update_data_p()
    return dumps(output)

#### NO NEED TO MODIFY BELOW THIS POINT

if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit_gracefully) # For coverage
    APP.run(port=config.port) # Do not edit this port
