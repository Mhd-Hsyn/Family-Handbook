import jwt
import datetime
import re
import random
from api.models import Auth, WhitelistToken
from PIL import Image
from decouple import config
import string
import secrets
from django.db.models import F,Sum,Prefetch
from api.models import (
    Auth
    )
from family_link.models import (
    Message
)
from family_link.serializers import (
    AuthSerializer, 
)
from family_registeration.models import FamilyMemberRegisterationDetail, FamilyParentRegisterationDetail
from FamFin.serializers import AuthsSerializer
import time
from django.conf import settings

def requireKeys(reqArray, requestData):
    try:
        for j in reqArray:
            if not j in requestData:
                return False
        return True

    except:
        return False


def allfieldsRequired(reqArray, requestData):
    try:
        for j in reqArray:
            if len(requestData[j]) == 0:
                return False

        return True

    except:
        return False


def checkemailforamt(email):
    emailregix = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    if re.match(emailregix, email):
        return True

    else:
        return False


def passwordLengthValidator(passwd):
    if len(passwd) >= 8 and len(passwd) <= 20:
        return True

    else:
        return False


##both keys and required field validation


def keyValidation(keyStatus, reqStatus, requestData, requireFields):
    ##keys validation
    if keyStatus:
        keysStataus = requireKeys(requireFields, requestData)
        if not keysStataus:
            return {
                "status": False,
                "message": f"{requireFields} all keys are required",
            }

    ##Required field validation
    if reqStatus:
        requiredStatus = allfieldsRequired(requireFields, requestData)
        if not requiredStatus:
            return {"status": False, "message": "All Fields are Required"}


def makedict(obj, key, imgkey=False):
    dictobj = {}

    for j in range(len(key)):
        keydata = getattr(obj, key[j])
        if keydata:
            dictobj[key[j]] = keydata

    if imgkey:
        imgUrl = getattr(obj, key[-1])
        if imgUrl:
            dictobj[key[-1]] = imgUrl.url
        else:
            dictobj[key[-1]] = ""

    return dictobj


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password


def exceptionhandler(val):
    error_messages = []

    if isinstance(val, dict):
        # If val is a dictionary, assume it's a custom validation result
        if "error" in val:
            error_messages.append(val["error"])
    else:
        # Otherwise, assume it's a serializer with errors attribute
        for field, errors in val.errors.items():
            # Customize the way you want to format each error message
            error_message = f"{field}: {', '.join(errors)}"
            error_messages.append(error_message)

    return ", ".join(error_messages)


def generatedToken(fetchuser, authKey, totaldays, request):
    try:
        access_token_payload = {
            "id": str(fetchuser.id),
            "email": fetchuser.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=totaldays),
            "iat": datetime.datetime.utcnow(),
        }

        userpayload = {
            "id": str(fetchuser.id),
            "full_name": fetchuser.full_name,
            "email": fetchuser.email,
        }

        access_token = jwt.encode(access_token_payload, authKey, algorithm="HS256")
        WhitelistToken.objects.create(auth= fetchuser, token = access_token)
        return {"status": True, "token": access_token, "payload": userpayload}

    except Exception as e:
        return {
            "status": False,
            "message": "Something went wrong in token creation",
            "details": str(e),
        }


def User_Token(fetchuser):
    """
    User Generate Token When User Login
    """
    try:
        secret_key = config("User_jwt_token")
        totaldays = 1
        token_payload = {
            "id": str(fetchuser.id),
            "email": fetchuser.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=totaldays),
            "iat": datetime.datetime.utcnow(),
        }
        detail_payload = {
            "id": str(fetchuser.id),
            "email": fetchuser.email,
            "fullname": fetchuser.full_name,
        }

        token = jwt.encode(token_payload, key=secret_key, algorithm="HS256")
        return {"status": True, "token": token, "payload": detail_payload}
    except Exception as e:
        return {"status": False, "message": f"Error during generationg token {str(e)}"}


def execptionhandler(val):
    if "error" in val.errors:
        error = val.errors["error"][0]
    else:
        key = next(iter(val.errors))
        error = key + ", " + val.errors[key][0]

    return error

# def blacklisttoken(id, token):
#     try:
#         whitelistToken.objects.get(user=id, token=token).delete()
#         return True

#     except:
#         return False


##chat
def chat_list_last_message(chat_list):
        for j in chat_list:
            last_chat = Message.objects.filter(room=j["personal_room"]).order_by('-created_at').first()
            if last_chat:
                j["last_message"] = last_chat.message
                j["message_type"] = last_chat.message_type
                j["audio_bytes"] = last_chat.audio_bytes
            else:
                j["message_type"] = "null"
                j["last_message"] = "-"


# def specific_user_chat_list(request, user_id):
#     user_list = Auth.objects.filter(
#         chat_room__participants=user_id
#     ).annotate(
#         personal_room=F('chat_room__id'),
#     ).order_by('-chat_room__updated_at').exclude(id = user_id )

#     print("user_list===",user_list)

#     user_list_serializer = AuthSerializer(user_list, many=True, context={'request': request})
#     chat_list_last_message(user_list_serializer.data)
    
#     return user_list_serializer.data


def specific_user_chat_list(request, user_id):
    user_list = Auth.objects.filter(
        chat_room__participants=user_id
    ).annotate(
        personal_room=F('chat_room__id'),
    ).order_by('-chat_room__updated_at').exclude(id=user_id).prefetch_related(
        Prefetch('fam_parent', queryset=FamilyParentRegisterationDetail.objects.all()),
        Prefetch('fam_members', queryset=FamilyMemberRegisterationDetail.objects.all())
    )

    user_list_serializer = AuthSerializer(user_list, many=True, context={'request': request})
    
    # Call the chat_list_last_message if needed
    chat_list_last_message(user_list_serializer.data)
    
    return user_list_serializer.data

def get_user_details(user_id):
    user = Auth.objects.get(id=user_id)
    user_data = AuthsSerializer(user).data
    user_data['profile'] = user.profile.url
    return user_data

def get_payment_details(payments, user_key):
    payment_info = payments.values(user_key).annotate(total_amount=Sum('amount'), created_at=F('created_at'), id=F('id'))
    return [
        {**get_user_details(entry[user_key]), 'total_amount': entry['total_amount'], 'created_at': entry['created_at'], 'id': entry['id']}
        for entry in payment_info
    ], sum(entry['total_amount'] for entry in payment_info)


def get_user_name(request, sender_id):

        full_name = None
        # Check in FamilyParentRegisterationDetail
        parent_user = FamilyParentRegisterationDetail.objects.filter(auth=sender_id).first()
        if parent_user:
            full_name = parent_user.name
        
        # If not found in parent table, check in member table
        if not full_name:
            member_user = FamilyMemberRegisterationDetail.objects.filter(auth=sender_id).first()
            if member_user:
                full_name = member_user.name

        return full_name


def generate_zegocloud_token(user_id):
    app_id = settings.ZEGOCLOUD_APP_ID
    server_secret = settings.ZEGOCLOUD_SERVER_SECRET
    expiration_time = int(time.time()) + 3600  # Token valid for 1 hour

    payload = {
        'app_id': app_id,
        'user_id': user_id,
        'exp': expiration_time
    }

    token = jwt.encode(payload, server_secret, algorithm='HS256')
    return token