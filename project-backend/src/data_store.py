'''
data_store.py

This contains a definition for a Datastore class which 
you should use to store your data. You don't need to 
understand how it works at this point, just how to use it :)

The data_store variable is global, meaning that so 
long as you import it into any python file in src, 
you can access its contents.

Example usage:

    from data_store import data_store

    store = data_store.get()
    print(store) # Prints { 'names': ['Nick', 'Emily', 'Hayden', 'Rob'] }

    names = store['names']

    names.remove('Rob')
    names.append('Jake')
    names.sort()

    print(store) # Prints { 'names': ['Emily', 'Hayden', 'Jake', 'Nick'] }
    data_store.set(store)
'''

## YOU SHOULD MODIFY THIS OBJECT BELOW
initial_object = {
    'users': [
       
    ],
    'handles' : {},
    'removed_users': [

    ],
    'admin_num' : 0,
    'channels': {
        
    },
    'channel_num' : 0,        
    'messages': {
        
    },
    'message_num' : 0,
    'dms':{

    },
    'dm_num' : 0,
    'active_sessions' : {

    },
    'session_num' : 0,
    'pass_reset_codes':{},

    #for the users stats
    'time_stamped':{
        'channel': 0,
        'message': 0,
        'dm': 0,
    },
    'channel_exists' : 0,
    'dm_exists' : 0,
    'message_exists' : 0,
    'channels_dict' : [],
    'dms_dict' : [],
    'messages_dict' : [],
   

}
## YOU SHOULD MODIFY THIS OBJECT ABOVE

class Datastore:
    def __init__(self):
        self.__store = initial_object

    def get(self):
        return self.__store

    def set(self, store):
        if not isinstance(store, dict):
            raise TypeError('store must be of type dictionary')
        self.__store = store

print('Loading Datastore...')

global data_store
data_store = Datastore()

