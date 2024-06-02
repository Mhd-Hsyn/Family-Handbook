from uuid import UUID
from rest_framework import serializers
from .Useable.prompts import getIntroPageNote
from api.models import (
    Auth,
    Role,
    Pdf,
    CoverPage,
    IntroductionPage,
    family_bios, 
    CoreValues,
    VisionStatements,
    MissionStatements,
    CodeOfConducts,
    FamilyMediaAgreements,
    FamilyConstitutions,
    Summary,

    parent_members, 
    other_members,
)
from passlib.hash import django_pbkdf2_sha256 as handler



class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ["full_name","email","password","address", "phone"]
    
    def validate(self, attrs):
        role = Role.objects.filter(value= "user").first()
        if not role:
            raise serializers.ValidationError("Role 'user' is not defined. Please contact the administrator.")
        attrs['role']= role
        return super().validate(attrs)

    def save(self, **kwargs):
        # Hash the password before saving
        password = self.validated_data.get("password")
        if password:
            self.validated_data["password"] = handler.hash(password)

        return super().save(**kwargs)



class UserAllPdfSerializer(serializers.ModelSerializer):
    """ 
    This serializer will give all FHB pdf's of the user 
    with status of pending or complete
    """
    status = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d %b, %Y")

    class Meta:
        model = Pdf
        # fields = "__all__"
        fields= ['id','status', 'created_at', 'name', 'family_type']

    def get_status(self, obj):
        # Check if all related objects have is_finished set to 1
        all_related_models = [
            CoverPage,
            IntroductionPage,
            family_bios, 
            CoreValues,
            VisionStatements,
            MissionStatements,
            CodeOfConducts,
            FamilyMediaAgreements,
            FamilyConstitutions,
            Summary,
        ]

        for model in all_related_models:
            related_objects = model.objects.filter(pdf_id=obj.id)
            if related_objects.exists():
                if related_objects.filter(is_finished=0).exists():
                    # If any related object has is_finished set to 0, return 0
                    return "pending"
            else :
                return "pending"
        # If all related objects have is_finished set to 1, return 1
        return "completed"


class UserCreatePdfSerializer(serializers.ModelSerializer):
    dir = serializers.CharField(required=False)
    class Meta:
        model= Pdf
        fields= ['name', 'dir', 'ip_address', 'font_style', 'user_id']

    def validate(self, data):
        user= self.context.get("user", None)
        if user:
            data['user_id'] = user
        else:
            raise serializers.ValidationError("User is None")

        if 'name' in data and 'dir' not in data:
            # Set 'dir' field to the same value as 'name' if 'dir' is not provided
            data['dir'] = data['name']
        return data


# Module No 1 CoverPage

class UploadCoverPageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverPage
        fields = ['pdf_id', 'image', 'is_finished']

    def create(self, validated_data):
        user_id = self.context.get("user_id")
        pdf_instance = validated_data.get("pdf_id")
        if not Pdf.objects.filter(id=pdf_instance.id, user_id=user_id).exists():
            raise serializers.ValidationError("The provided PDF does not exist for this user.")
        return CoverPage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Perform update logic here
        instance.image = validated_data.get('image', instance.image)
        if all(getattr(instance, field) for field in ['image']):
            instance.is_finished = 1
        else:
            instance.is_finished = 0
        instance.save()
        return instance



class PDFCoverPageSerializer(serializers.ModelSerializer):
    sub_title= serializers.CharField(required= False)
    sentence= serializers.CharField(required= False)
    class Meta:
        model = CoverPage
        fields= ['pdf_id', 'lastname','lastname_heading', 'sentence', 'is_finished', 'sub_title']

    def create(self, validated_data):
        user_id = self.context.get("user_id")
        pdf_instance = validated_data.get("pdf_id")
        if not Pdf.objects.filter(id=pdf_instance.id, user_id=user_id).exists():
            raise serializers.ValidationError("The provided PDF does not exist for this user.")
        return CoverPage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        if all(getattr(instance, field) for field in ['image']):
            instance.is_finished = 1
        else:
            instance.is_finished = 0
        instance.save()
        return instance


class GetCoverPageSerializer(serializers.ModelSerializer):
    created_at= serializers.DateTimeField(format="%d %b, %Y")
    class Meta:
        model = CoverPage
        exclude= ['updated_at', 'id']


# Module No. 2 Introduction Page
class GetIntroPageSer(serializers.ModelSerializer):
    class Meta:
        model= IntroductionPage
        fields= "__all__"
    

class ADDIntroPageSerializer(serializers.ModelSerializer):
    character_list = serializers.ListField(child=serializers.CharField())
    class Meta:
        model= IntroductionPage
        fields= '__all__'
    
    def validate(self, attrs):
        # Here the ChatGPT will be integrated and the is_finished logic also implemented
        beginning_letter= attrs['beginning_letter']
        tone_used= attrs['tone_used']
        characters_list= attrs.pop('character_list')
        if not type(characters_list) == list:
            raise serializers.ValidationError("characters_list must be in list format")

        characters_list_str = ', '.join(str(character) for character in characters_list)
        family_name= attrs['pdf_id'].user_id.full_name

        fetch_coverpage= CoverPage.objects.filter(pdf_id=attrs['pdf_id']).first()
        if fetch_coverpage:
            family_name= fetch_coverpage.lastname
        else:
            family_name= attrs['pdf_id'].user_id.full_name

        note= getIntroPageNote(
            starting=beginning_letter,
            family_name=family_name,
            tone=tone_used,
            chatacters_list=characters_list_str
            )
        attrs['note']= note
        attrs['characters_list']= characters_list
        return super().validate(attrs)

    
    def update(self, instance, validated_data):
        instance.__dict__.update(**validated_data)
        instance.save()
        return instance



class SaveInroNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model= IntroductionPage
        fields= ['note']

    def update(self, instance, validated_data):
        instance.note = validated_data.get('note', instance.note)
        instance.save()

        # Check if all fields are filled and update is_finished accordingly
        all_fields_filled = all(
            getattr(instance, field) for field in ['beginning_letter', 'tone_used', 'note', 'characters_list']
        )
        instance.is_finished = 1 if all_fields_filled else 0
        instance.save()

        return instance



# Module No. 03    FAMILY MEMBERS

# For Parents
class AddParentMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = parent_members
        fields = [
            'family_bios_id', 'image', 'relation', 'other_relation', 'full_name', 'street_address', 
            'birth_city', 'city', 'email', 'dob', 'profession', 
            'favourite_food', 'other_favourite_food', 'favourite_holiday', 
            'other_favourite_holiday', 'afraid_of', 'other_afraid_of', 
            'favourite_quote', 'other_favourite_quote'
        ]

    def validate(self, data):
        family_bios_id= self.context.get("family_bios_id", None)
        if family_bios_id is None:
            raise serializers.ValidationError("problem in fetching or creating family_bios_id")
        
        data['family_bios_id']= family_bios_id

        # Check that only one of the required pairs is provided
        if not data.get('relation') and not data.get('other_relation'):
            raise serializers.ValidationError("Either 'relation' or 'other_relation' must be provided.")
        
        if not data.get('favourite_food') and not data.get('other_favourite_food'):
            raise serializers.ValidationError("Either 'favourite_food' or 'other_favourite_food' must be provided.")
        
        if not data.get('favourite_holiday') and not data.get('other_favourite_holiday'):
            raise serializers.ValidationError("Either 'favourite_holiday' or 'other_favourite_holiday' must be provided.")
        
        if not data.get('afraid_of') and not data.get('other_afraid_of'):
            raise serializers.ValidationError("Either 'afraid_of' or 'other_afraid_of' must be provided.")
        
        if not data.get('favourite_quote') and not data.get('other_favourite_quote'):
            raise serializers.ValidationError("Either 'favourite_quote' or 'other_favourite_quote' must be provided.")

        if data.get('favourite_quote') or data.get('other_favourite_quote'):
            data['is_quote'] = 1
        
        else:
            data['is_quote'] = 0

        return data

    def create(self, validated_data):
        return parent_members.objects.create(**validated_data)


class GetParentMemberSerializer(serializers.ModelSerializer):
    parent_id= serializers.IntegerField(source= 'id')
    class Meta:
        model = parent_members
        exclude = ['id', 'created_at', 'updated_at', 'is_quote', 'family_bios_id']

    # def to_representation(self, instance):
    #     """
    #     Object instance -> Dict of primitive datatypes.
    #     This method is responsible for converting the model instance into a dictionary of primitive data types.
    #     """
    #     representation = super().to_representation(instance)
    #     # Filter out fields with None values
    #     filtered_representation = {key: value for key, value in representation.items() if value is not None and value is not ""}
    #     return filtered_representation



class UpdateParentMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = parent_members
        fields = [
            'image', 'relation', 'other_relation', 'full_name', 'street_address', 
            'birth_city', 'city', 'email', 'dob', 'profession', 
            'favourite_food', 'other_favourite_food', 'favourite_holiday', 
            'other_favourite_holiday', 'afraid_of', 'other_afraid_of', 
            'favourite_quote', 'other_favourite_quote'
        ]

    def validate(self, data):

        # Check that only one of the required pairs is provided
        if not data.get('relation') and not data.get('other_relation'):
            raise serializers.ValidationError("Either 'relation' or 'other_relation' must be provided.")
        
        if not data.get('favourite_food') and not data.get('other_favourite_food'):
            raise serializers.ValidationError("Either 'favourite_food' or 'other_favourite_food' must be provided.")
        
        if not data.get('favourite_holiday') and not data.get('other_favourite_holiday'):
            raise serializers.ValidationError("Either 'favourite_holiday' or 'other_favourite_holiday' must be provided.")
        
        if not data.get('afraid_of') and not data.get('other_afraid_of'):
            raise serializers.ValidationError("Either 'afraid_of' or 'other_afraid_of' must be provided.")
        
        if not data.get('favourite_quote') and not data.get('other_favourite_quote'):
            raise serializers.ValidationError("Either 'favourite_quote' or 'other_favourite_quote' must be provided.")

        if data.get('favourite_quote') or data.get('other_favourite_quote'):
            data['is_quote'] = 1
        
        else:
            data['is_quote'] = 0

        return data





# Module No. 04    CORE VALUE
class CoreValueSer(serializers.ModelSerializer):
    class Meta:
        model = CoreValues
        fields= ['pdf_id', 'value_one', 'value_two', 'value_three', 'value_four', 'value_five', 'note', 'is_finished']



# Module No. 05    Vision Statements
class VissionStatSerializer(serializers.ModelSerializer):
    class Meta:
        model= VisionStatements
        fields= ['pdf_id', 'is_finished', 'heading', 'note'] 

class GETVissionStatSerializer(serializers.ModelSerializer):
    class Meta:
        model= VisionStatements
        fields= ['heading', 'note'] 


# Module No. 06    Mission Statements
class MissionStatSerializer(serializers.ModelSerializer):
    class Meta:
        model= MissionStatements
        fields= ['pdf_id', 'is_finished', 'heading', 'note']

class GETMissionStatSerializer(serializers.ModelSerializer):
    class Meta:
        model= MissionStatements
        fields= ['heading', 'note']

# Module No 7     Code of Conduct
class AddCodeOfConductSer(serializers.ModelSerializer):
    class Meta:
        model= CodeOfConducts
        fields= "__all__"

class GetCodeOfConductSer(serializers.ModelSerializer):
    class Meta:
        model= CodeOfConducts
        exclude= ['id', 'created_at', 'updated_at', 'is_finished', 'pdf_id']

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     return {key: value for key, value in data.items() if value is not ""}



# Module No 8     Family Media Aggrement
class AddFamilyMediaAggrementSerializer(serializers.ModelSerializer):
    class Meta:
        model= FamilyMediaAgreements
        fields= "__all__"

class GetAddFamilyMediaAggrementSerializer(serializers.ModelSerializer):
    class Meta:
        model= FamilyMediaAgreements
        exclude= ['id', 'created_at', 'updated_at', 'is_finished', 'pdf_id']



# Module No. 9      Family Constitution
class AddFamilyConstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model= FamilyConstitutions
        fields= "__all__"

class GetFamilyConstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model= FamilyConstitutions
        exclude= ['id', 'created_at', 'updated_at', 'is_finished', 'pdf_id']



# Module No. 10      Family Book Summary
class AddFamilyBookSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model= Summary
        fields= "__all__"

class GetFamilyBookSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model= Summary
        exclude= ['id', 'created_at', 'updated_at', 'is_finished', 'pdf_id']