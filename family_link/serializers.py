from api.models import Auth
from family_registeration.models import (FamilyMemberRegisterationDetail,
                                         FamilyParentRegisterationDetail,
                                         FamilyRelationship)
from family_registeration.serializers import (
    FamilyMemberRegisterationDetailSerializer,
    FamilyParentRegisterationDetailSerializer)
from rest_framework import serializers

from .models import Message


class AuthSerializer(serializers.ModelSerializer):
    # profile = serializers.SerializerMethodField()
    personal_room = serializers.CharField()
    # full_name = serializers.SerializerMethodField()
    family_member_name = serializers.SerializerMethodField()
    family_member_picture = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    message_type = serializers.SerializerMethodField()
    audio_bytes = serializers.SerializerMethodField()

    # def get_profile(self, user):
    #     return user.profile.url if user.profile else None

    # def get_full_name(self, user):
    #     return user.full_name

    def get_family_member_name(self, user):
        # Get the first family member's name, if available
        first_parent = user.fam_parent.first()
        if first_parent:
            return first_parent.name
        first_member = user.fam_members.first()
        if first_member:
            return first_member.name
        return None

    def get_family_member_picture(self, user):
        # Get the first family member's picture, if available
        first_parent = user.fam_parent.first()
        if first_parent:
            return first_parent.picture.url if first_parent.picture else None
        first_member = user.fam_members.first()
        if first_member:
            return first_member.picture.url if first_member.picture else None
        return None

    def get_last_message(self, user):
        # Assuming last message is stored in the chat room model
        last_message = user.chat_room.last().last_message if user.chat_room.exists() else ""
        return last_message

    def get_message_type(self, user):
        # Implement your logic for message type
        return "text"  # Example, change it accordingly

    def get_audio_bytes(self, user):
        # Implement your logic for audio bytes
        return ""  # Example, change it accordingly

    class Meta:
        model = Auth
        fields = [
            'id', 'email', 'personal_room', 'family_member_name', 'family_member_picture',
             'last_message', 'message_type', 'audio_bytes'
        ]



class MessageCreateSerializer(serializers.Serializer):
    receiver = serializers.CharField()
    message_type = serializers.CharField(max_length=5)
    message = serializers.CharField(required=False)
    file = serializers.FileField(required=False)
    audio_bytes = serializers.CharField(required=False)

    def validate(self, data):
        message_type = data.get('message_type')
        valid_message_types = ["text", "audio", "image","docs"]
        if message_type not in valid_message_types:
            raise serializers.ValidationError("Invalid message_type. Allowed values are: text, audio, image,docs")
        
        elif message_type == 'text':
            if 'audio_bytes' in data:
                raise serializers.ValidationError("Audio bytes should not be included when message_type is 'text'.")
            if 'file' in data:
                raise serializers.ValidationError("File should not be included when message_type is 'text'.")
        
        elif message_type == 'image':
            if 'audio_bytes' in data:
                raise serializers.ValidationError("Audio bytes should not be included when message_type is 'image'.")
            if 'file' not in data:
                raise serializers.ValidationError("File is required when message_type is 'file'.")
       
        elif message_type == 'audio':
            if 'file' in data:
                raise serializers.ValidationError("File should not be included when message_type is 'audio'.")
            if 'audio_bytes' not in data:
                raise serializers.ValidationError("Audio bytes are required when message_type is 'audio'.")
            
        return data


class GetMessageSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField() 

    class Meta:
        model = Message
        fields = ('id', 'sender', 'message', 'message_type', 'file','filename', 'full_name','audio_bytes')
 
    # def get_full_name(self, obj):
    #     return f"{obj.sender.full_name}"
    
    def get_file(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
            # return (obj.file.url)
        
        return None
    
    def get_filename(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return obj.file.name
        
        return None

    def get_full_name(self, obj):
        sender_id = obj.sender
        parent_user = FamilyParentRegisterationDetail.objects.filter(auth=sender_id).first()
        if parent_user:
            return parent_user.name
        
        member_user = FamilyMemberRegisterationDetail.objects.filter(auth=sender_id).first()
        if member_user:
            return member_user.name

        return None
    
 
class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        parent_user = FamilyParentRegisterationDetail.objects.filter(auth=obj).first()
        if parent_user:
            return parent_user.name
        
        member_user = FamilyMemberRegisterationDetail.objects.filter(auth=obj).first()
        if member_user:
            return member_user.name

        return None

    def get_picture(self, obj):
        request = self.context.get('request')
        parent_user = FamilyParentRegisterationDetail.objects.filter(auth=obj).first()
        if parent_user:
            if request:
                return request.build_absolute_uri(parent_user.picture.url)
            return parent_user.picture.url
        
        member_user = FamilyMemberRegisterationDetail.objects.filter(auth=obj).first()
        if member_user:
            if request:
                return request.build_absolute_uri(member_user.picture.url)
            return member_user.picture.url

        return None
    

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyParentRegisterationDetail
        fields = ['id', 'name', 'auth'] 

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ['id', 'name', 'auth'] 

class FamilyRelationshipSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(read_only=True)
    members = FamilyMemberSerializer(many=True, read_only=True)

    class Meta:
        model = FamilyRelationship
        fields = ['id', 'parent', 'members',]  



