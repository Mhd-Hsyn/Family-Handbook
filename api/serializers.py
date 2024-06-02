# serializers.py
from rest_framework import serializers
from .models import Auth,FamilyDetails,LogoSymbol,LogoColor,LogoSvg,RelatedSvg
from passlib.hash import django_pbkdf2_sha256 as handler


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ["full_name","email","password"]

    def save(self, **kwargs):
        # Hash the password before saving
        password = self.validated_data.get("password")
        if password:
            self.validated_data["password"] = handler.hash(password)

        return super().save(**kwargs)


class LoginSerializer(serializers.Serializer):
    class Meta:
        model = Auth
        fields = ["email", "password"]


class FamilyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyDetails
        fields = ['family_last_name', 'slogan', 'auth']


class LogoSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogoSymbol
        fields = ["id","symbol_name", "symbol"]


class LogoColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogoColor
        fields = ["id","name", "code"]


class LogoSvgSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogoSvg
        fields = ["id","svg_code","logo"]


class RelatedSvgSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedSvg
        fields = ["id","svg_code",'logo']