from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from passlib.hash import django_pbkdf2_sha256 as handler
from api.models import Auth
from .models import (
    FamilyParentRegisterationDetail,
    FamilyMemberRegisterationDetail,
    
)


class FamilyRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyParentRegisterationDetail
        fields = ['family_role', 'name', "birth_city", "current_city", 'date_of_birth', 'profession', 'vision', 'mission', 'goals', 'picture']



class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ['family_role', 'name']

class MultipleMemberSerializer(serializers.Serializer):
    members = MemberSerializer(many=True)


class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ['email', 'password']
    
    def save(self, **kwargs):
        # Hash the password before saving
        password = self.validated_data.get("password")
        if password:
            self.validated_data["password"] = handler.hash(password)

        return super().save(**kwargs)


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    auth = serializers.PrimaryKeyRelatedField(queryset=Auth.objects.all(), required=False)

    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ["family_role", "name", "birth_city", "current_city", "date_of_birth", "profession", "picture", "email", "password", "auth"]

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        auth_user = Auth(
            email=email,
            password=handler.hash(password)
        )
        auth_user.save()
        validated_data['auth'] = auth_user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        auth_instance = instance.auth

        if 'email' in validated_data or 'password' in validated_data:
            if auth_instance:
                auth_data = {
                    'email': validated_data.pop('email', auth_instance.email),
                    'password': handler.hash(validated_data.pop('password', auth_instance.password))
                }
                auth_serializer = AuthSerializer(auth_instance, data=auth_data, partial=True)
                if auth_serializer.is_valid():
                    auth_serializer.save()
            else:
                email = validated_data.pop('email')
                password = validated_data.pop('password')
                auth_instance = Auth(
                    email=email,
                    password=handler.hash(password)
                )
                auth_instance.save()
                instance.auth = auth_instance

        instance.birth_city = validated_data.get("birth_city", instance.birth_city)
        instance.current_city = validated_data.get("current_city", instance.current_city)
        instance.date_of_birth = validated_data.get("date_of_birth", instance.date_of_birth)
        instance.profession = validated_data.get("profession", instance.profession)
        instance.picture = validated_data.get("picture", instance.picture)
        instance.save()
        return instance

# class FamilyParentRegisterationDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FamilyParentRegisterationDetail
#         fields = ['family_role', 'name', 'birth_city', 'current_city', 'date_of_birth', 'profession', 'vision', 'mission', 'goals']

# class FamilyMemberRegisterationDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FamilyMemberRegisterationDetail
#         fields = ['family_role', 'name', 'birth_city', 'current_city', 'date_of_birth', 'profession']



class FamilyParentRegisterationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyParentRegisterationDetail
        fields = ['family_role', 'name']

class FamilyMemberRegisterationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMemberRegisterationDetail
        fields = ['family_role', 'name']