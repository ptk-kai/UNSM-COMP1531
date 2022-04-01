1) Channels can have the same channel name as the channel id is unique.

2) If handle generation creates a handle that is an empty string (“”), 
    an InputError is raised.
    - This occurs if name_first and name_last consist solely of non-alphanumeric
      characters.
      
3) Special characters are allowed in name_first and name_last

4) Any channel_id or auth_user_id that is registered is valid

5) When channel_messages_v1 returns 50 messages, it will include the message
   with the start id, but exclude the message with id start + 50
    - E.g. If start = 0, messages with ids 0-49 will be returned 
    
6) The owner is stored separately from the rest of the members in the
     data store. 

7) If the original handle_str ends with a number and is a duplicate, a new
   number will be appended onto the end. 
   - E.g. If name_first = steve and name_last = smith2 but stevesmith2 is 
   already taken, the handle stevesmith20 will be created. If stevesmith20 
   is taken, it will be incremented to stevesmith21.
