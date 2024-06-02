from rest_framework import serializers
from family_registeration.models import FamilyMemberRegisterationDetail
from api.models import Auth
from family_registeration.models import FamilyParentRegisterationDetail

class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ["id", "full_name", "profile", "email"]


class FamilyMemberSerializer(serializers.ModelSerializer):
    auth = serializers.SerializerMethodField()

    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ["auth"]

    def get_auth(self, obj):
        auth_instance = Auth.objects.get(id=obj.auth_id)
        return AuthSerializer(auth_instance).data


class AuthsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ["full_name", "profile"]


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = "__all__"



class FamilyParentRegisterationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyParentRegisterationDetail
        fields = ['family_role', 'name']

class FamilyMemberRegisterationDetailSerializer(serializers.ModelSerializer):
    auth_id = serializers.CharField()

    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ['id', 'family_role', 'name', 'picture', 'auth_id']