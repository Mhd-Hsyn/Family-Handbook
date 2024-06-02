# import requests
# from decouple import config
# import json
  
# def trigger_reciever_notification(channel_name:str,chat_payload:dict):
#     url = f"{config('socketslink')}/trigger_notification/{channel_name}"
#     headers = {
#     'Content-Type': 'application/json'
#     }
#     response = requests.request("POST", url, headers=headers, data=chat_payload)
#     print(response.json())


# def trigger_reciever_room(channel_name:str,chat_payload:list):
#     url = f"{config('socketslink')}/trigger_room/{channel_name}"
#     headers = {
#     'Content-Type': 'application/json'
#     }
#     for item in chat_payload:
#         item['personal_room'] = str(item['personal_room'])
#         item['id'] = str(item['id'])
    
#     chat_payload = json.dumps({"payload":chat_payload})
#     response = requests.request("POST", url, headers=headers, data=chat_payload)
#     print(response.json())


import requests
from decouple import config
import json
   

def trigger_emit_chat(channel_name:str,data:dict):
    print("======== trigger_emit_chat ========")
    url = "http://167.114.96.66:5006/emit_chat/"

    payload = json.dumps({
    "message_obj": {
        "channel_name": str(channel_name),
        "message": data
        # "message": data['message']
    }
    })

    # print("payload=============",payload)

    headers = {
        'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print("response=============",response.text)