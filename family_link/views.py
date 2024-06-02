from uuid import UUID

from api.models import Auth
from core.helper import (exceptionhandler, get_user_name, keyValidation,
                         specific_user_chat_list, generate_zegocloud_token)
from core.permissions import authorization
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Count
from django.http import HttpResponse
from family_registeration.models import ( FamilyRelationship)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Chat_Room, Message
from .serializers import (GetMessageSerializer,
                          MessageCreateSerializer, UserSerializer)
from .trigger import trigger_emit_chat


# Create your views here.
def index(request):
    return HttpResponse("<h1>Project Family Handbook --Family Link</h1>")



class ChatViewset(ModelViewSet):

    @action(detail=False, methods=['GET'],permission_classes = [authorization])
    def specific_user_list(self, request):
        try:
            user_id = request.GET["token"]["id"]
            user_list = specific_user_chat_list(request,user_id)
            return Response({"status":True,"data":user_list})

        except Exception as e:
            return Response({'status':False,'errors':str(e)},status=500)

    @action(detail=False, methods=['GET'], permission_classes=[authorization])
    def all_users(self, request):
        try:
            # Get authenticated user's ID
            user_id = UUID(request.GET.get("token").get("id"))

            # Fetch relationships where the authenticated user is a parent or member
            relationships = FamilyRelationship.objects.filter(
                Q(parent__auth__id=user_id) | Q(members__auth__id=user_id)
            ).select_related('parent').prefetch_related('members')

            # Get unique user IDs excluding the authenticated user
            user_ids = set()
            for relationship in relationships:
                if relationship.parent.auth.id != user_id:
                    user_ids.add(relationship.parent.auth.id)
                for member in relationship.members.all():
                    if member.auth.id != user_id:
                        user_ids.add(member.auth.id)

            # Fetch email addresses of all users except the authenticated user
            users_emails = Auth.objects.filter(id__in=user_ids).exclude(id=user_id)
            serialized_data = UserSerializer(users_emails, many=True)

            return Response({"status": True, "data": serialized_data.data}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": False, "errors": "Object does not exist."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"status": False, "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['POST'],permission_classes = [authorization])
    def send_message(self,request):
        message_serializer = MessageCreateSerializer(data=request.data)
        if not message_serializer.is_valid():
            error = exceptionhandler(message_serializer)
            return Response({"status": False, "message": error}, status=422)
        
        sender_id = request.GET["token"]["id"]
        receiver_id = message_serializer.data["receiver"]
        message =  message_serializer.data.get("message")
        # message =  message_serializer.data.get("message","-")
        message_type = message_serializer.data["message_type"]
        file = request.data.get("file",False)
        audio_bytes = request.data.get("audio_bytes",False)
        fileurl = "null"
        filename = "null"
        audio_data = False
        chat_room = Chat_Room.objects.filter(participants__id = sender_id).filter(participants__id = receiver_id).first()
        if not chat_room:
            return Response({"status":False,"message":"Chat room not found please first create a chat room first"},400)
        
        sender_account = Auth.objects.get(id = sender_id)
        create_message = Message(room = chat_room,sender = sender_account,message = message,message_type = message_type,file=file if file else None,audio_bytes = audio_bytes if audio_bytes else None)
        create_message.save()

        if file:
            fileurl = f'{request.META["wsgi.url_scheme"]}://{request.META["HTTP_HOST"]}{create_message.file.url}'
            # fileurl = f'{request.META["HTTP_HOST"]}{create_message.file.url}'
            # fileurl = f'{create_message.file.url}'
            # remove_extra_characters it removes extra characters from url before file extension
            # fileurl = remove_extra_characters(fileurl)

            
            filename = create_message.file.name

        
        if audio_bytes:
            audio_data = audio_bytes



        message_data = {
            "message_id":str(create_message.id),
            "sender":sender_id,
            "receiver":receiver_id,
            "message":message,
            "message_type":message_type,
            "file":fileurl,
            "full_name":get_user_name(request, sender_id),
            "audio_bytes":audio_data,
            "filename":filename,
            "created_at":str(create_message.created_at)

        }
        #trigger chat room
        trigger_emit_chat(f"private_chat__{chat_room.id}", message_data)
        
        # trigger_emit_chat(f"private_chat__{chat_room.id}",json.dumps(message_data))

        # chat_list = list(.specific_user_chat_list(request,receiver_id))
        # #trigger reciever room
        # trigger_reciever_room(f"personal_room__{receiver_id}",chat_list)
        
        return Response({"status":True,"message":"Message created successfully","message_data":message_data},201)
        # return Response({"status":"OK"})


    @action(detail=False, methods=['GET'],permission_classes = [authorization])
    def get_message(self,request):
        sender_id = request.GET["token"]["id"]
        receiver_id = request.GET["receiver"]
        chat_room = Chat_Room.objects.filter(participants = sender_id).filter(participants = receiver_id).first()
        if not chat_room:
            return Response({"status":False,"message":"Chat room not found please first create a chat room first"},400)


        messages_list = Message.objects.filter(room=chat_room.id).order_by('created_at')
        serializer = GetMessageSerializer(messages_list, many=True,context={'request': request})
        return Response({"status":True,"data":serializer.data})


    @action(detail=False, methods=['GET'],permission_classes = [authorization])
    def specific_user_detail(self, request):
        try:
            user_id = request.GET["token"]["id"]
            userobj = Auth.objects.filter(id=user_id).first()
            user_serializer = UserSerializer(userobj)

            return Response({"status":True,"data":user_serializer.data})

        except Exception as e:
            return Response({'status':False,'errors':str(e)},status=500)


    @action(detail=False, methods=['POST'], permission_classes=[authorization])
    def create_room(self, request):
        try:
            first = request.GET["token"]["id"]
            second = request.GET["user_id"]

            user_ids = [first, second]  # add ids of users

            # Check if a chat room with the given participants already exists
            # existing_chat_room = Chat_Room.objects.filter(participants__in=user_ids)
            # existing_chat_room = Chat_Room.objects.filter(participants__in=user_ids).annotate(num_participants=Count('participants')).filter(num_participants=len(user_ids)).distinct()
            existing_chat_room = Chat_Room.objects.filter(
                participants__id=first
            ).filter(
                participants__id=second
            ).distinct()

            if not existing_chat_room.exists():
                # If the chat room doesn't exist, create a new one
                chat_room = Chat_Room.objects.create()

                # Add participants to the chat room
                chat_room.participants.add(*user_ids)

                # Save the chat room to persist changes
                chat_room.save()

            return Response({"status": True, "data": "Chat room created successfully"}, status=200)

        except Exception as e:
            # Handle exceptions appropriately
            return Response({"status": False, "error": str(e)}, status=500)

    @action(detail=False, methods=['POST'], permission_classes=[authorization])
    def create_room_group(self, request):
        try:
            # Get the user ID from the token
            user_id = request.GET["token"]["id"] # Assuming the user ID is in the token

            # Get the list of other user IDs from the request data
            other_user_ids = request.data.get('user_ids', [])

            if not other_user_ids:
                return Response({"status": False, "error": "At least one other user ID is required"}, status=400)

            # Combine the user ID from the token with the other user IDs
            user_ids = [user_id] + other_user_ids

            # Ensure all user IDs are valid UUIDs and not None
            user_ids = [str(uid) for uid in user_ids if uid is not None]

            if len(user_ids) < 2:
                return Response({"status": False, "error": "At least one other valid user ID is required"}, status=400)

            user_ids.sort()

            # Check if a chat room with exactly the given participants already exists
            existing_chat_rooms = Chat_Room.objects.filter(participants__in=user_ids)

            print("existing_chat_rooms===",existing_chat_rooms)

            for room in existing_chat_rooms:
                room_participants = list(room.participants.values_list('id', flat=True))
                room_participants = [str(participant) for participant in room_participants if participant is not None]
                room_participants.sort()

                if room_participants == user_ids:
                    return Response({"status": True, "data": "Chat room already exists"}, status=200)

            # Create a new room only if no existing room matches the participants exactly
            chat_room = Chat_Room.objects.create()

            # Add participants to the chat room
            chat_room.participants.add(*user_ids)

            # Save the chat room to persist changes
            chat_room.save()

            return Response({"status": True, "data": "Chat room created successfully"}, status=200)

        except Exception as e:
            # Handle exceptions appropriately
            return Response({"status": False, "error": str(e)}, status=500)


    @action(detail=False, methods=['GET'], permission_classes=[authorization])
    def call(self, request):
        user_id = request.GET["token"]["id"]
        token = generate_zegocloud_token(user_id)
        userobj = Auth.objects.filter(id=user_id).first()
        user_serializer = UserSerializer(userobj)
        return Response({"status": True, 'user_id': user_serializer.data['id'], 'user_name': user_serializer.data['full_name'], 'token': token}, status=200)
 