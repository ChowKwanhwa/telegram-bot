# from telethon import TelegramClient
# from telethon.sessions import StringSession

# api_id = 22453265
# api_hash = '641c3fad1c94728381a70113c70cd52d'

# with TelegramClient(StringSession(), api_id, api_hash) as client:
#     print("Your session file has been created successfully")
#     session_string = client.session.save()
#     print(f"Your session string is: {session_string}")


from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 22453265
api_hash = '641c3fad1c94728381a70113c70cd52d'

with TelegramClient("session", api_id, api_hash) as client:
    print("Your session file has been created successfully")
    
