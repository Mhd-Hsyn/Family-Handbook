"""
Views for the Django application.
"""
import os
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from decouple import config
from api.models import (
    Auth,
    FamilyDetails,
    LogoSymbol,
    LogoColor,
    LogoSvg,
    RelatedSvg,
    UserLogo
) 
from core.helper import (
    keyValidation,
    exceptionhandler,
    generatedToken,
    checkemailforamt,
    passwordLengthValidator
)   
from core.sendemail import sendotp
from core.permissions import authorization
from api.serializers import (
    RegisterSerializer,
    LoginSerializer,
    FamilyDetailsSerializer,
    LogoSymbolSerializer,
    LogoColorSerializer,
    LogoSvgSerializer,
    RelatedSvgSerializer
)
from passlib.hash import django_pbkdf2_sha256 as handler
from django.conf import settings
import random
from random import shuffle
import random
import ast

# Create your views here.


def index(request):
    return HttpResponse("<h1>Project family-handbook</h1>")


class AuthViewset(ModelViewSet):
    @action(detail=False, methods=["POST"])
    def signup(self, request):
        try:
            required_fields = ["full_name","email","password"]
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(
                    {"status": False, "message": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ser = RegisterSerializer(data=request.data)
            if ser.is_valid():
                ser.save()

                return Response(
                    {"status": True, "message": "Account created successfully"},
                    status=status.HTTP_201_CREATED,
                )

            else:
                error_message = exceptionhandler(ser)
                return Response(
                    {"status": False, "message": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
 
    @action(detail=False, methods=["post"])
    def login(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            email = request.data["email"]
            password = request.data["password"]

            user = Auth.objects.filter(email=email).first()

            if user and handler.verify(password, user.password):
                generate_auth = generatedToken(
                    user, config("User_jwt_token"), 1, request
                )

                if generate_auth["status"]:
                    user.no_of_wrong_attempts = 0
                    user.save()
                    return Response(
                        {
                            "status": True,
                            "message": "Login SuccessFully",
                            "token": generate_auth["token"],
                            "data": generate_auth["payload"],
                        },
                        status=status.HTTP_200_OK,
                    )

                else:
                    return Response(generate_auth)

            else:
                if user:
                    if user.no_of_wrong_attempts == user.no_of_attempts_allowed:
                        user.status = False
                    else:
                        user.no_of_wrong_attempts += 1

                    user.save()
                    if not user.status:
                        return Response(
                            {"status": False, "message": "Your Account is disable"},
                            403,
                        )

                return Response(
                    {"status": False, "message": "Invalid Credential"}, status=401
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)

    @action(detail=False, methods=["post"])
    def send_forget_otp(self, request):
        try:
            requireFields = ["email"]
            validator = keyValidation(True, True, request.data, requireFields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            else:
                email = request.data["email"]
                emailstatus = checkemailforamt(email)
                if not emailstatus:
                    return Response(
                        {"status": False, "message": "Email format is incorrect"}
                    )

                fetchadmin = Auth.objects.filter(email=email).first()
                if fetchadmin:
                    token = random.randrange(100000, 999999, 6)
                    fetchadmin.otp = token
                    fetchadmin.otp_count = 0
                    fetchadmin.otp_status = True
                    fetchadmin.save()
                    emailstatus = sendotp(email,token)
                    if emailstatus:
                        return Response(
                            {
                                "status": True,
                                "message": "Email send successfully",
                                "email": fetchadmin.email,
                            }
                        )

                    else:
                        return Response(
                            {"status": False, "message": "Something went wrong"},status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    return Response({"status": False, "message": "Email doesnot exist"},status=404)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)

    @action(detail=False, methods=["POST"])
    def verify_otp(self, request):
        try:
            ##validator keys and required
            requireFields = ["otp", "email"]
            validator = keyValidation(True, True, request.data, requireFields)

            if validator:
                return Response(validator,status=status.HTTP_400_BAD_REQUEST)

            else:
                otp = request.data["otp"]
                email = request.data["email"]
                fetchuser = Auth.objects.filter(email=email).first()
                if fetchuser:
                    if fetchuser.otp_status and fetchuser.otp_count < 3:
                        if fetchuser.otp == int(otp):
                            fetchuser.otp = 0
                            fetchuser.otp_status = True
                            fetchuser.save()
                            return Response(
                                {
                                    "status": True,
                                    "message": "Otp verified",
                                    "email": str(fetchuser.email),
                                },
                                status=status.HTTP_200_OK,
                            )
                        else:
                            fetchuser.otp_count += 1
                            fetchuser.save()
                            if fetchuser.otp_count >= 3:
                                fetchuser.otp = 0
                                fetchuser.otp_count = 0
                                fetchuser.otp_status = False
                                fetchuser.save()
                                return Response(
                                    {
                                        "status": False,
                                        "message": f"Your OTP is expired . . . Kindly get OTP again",
                                    },status=status.HTTP_400_BAD_REQUEST
                                )
                            return Response(
                                {
                                    "status": False,
                                    "message": f"Your OTP is wrong . You have only {3- fetchuser.otp_count} attempts left ",
                                },status=status.HTTP_400_BAD_REQUEST
                            )
                    return Response(
                        {
                            "status": False,
                            "message": "Your OTP is expired . . . Kindly get OTP again",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {"status": False, "message": "User not exist"}, status=404
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)

    @action(detail=False, methods=["POST"])
    def update_password(self, request):
        try:
            requireFeild = ["email", "newpassword"]
            validator = keyValidation(True, True, request.data, requireFeild)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            email = request.data["email"]
            newpassword = request.data["newpassword"]
            if not passwordLengthValidator(newpassword):
                return Response(
                    {
                        "status": False,
                        "error": "Password length must be greater than 8",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fetchuser = Auth.objects.filter(email=email).first()
            if fetchuser:
                if fetchuser.otp_status and fetchuser.otp == 0:
                    fetchuser.password = handler.hash(newpassword)
                    fetchuser.otp_status = False
                    fetchuser.otp_count = 0
                    fetchuser.save()
                    return Response(
                        {
                            "status": True,
                            "message": "Password updates successfully ",
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"status": False, "message": "Token not verified !!!!"}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"status": False, "message": "User Not Exist !!!"}, status=404
            )
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

import xml.etree.ElementTree as ET


class LogoDetails(ModelViewSet):
    
    @action(detail=False, methods=["GET"],permission_classes = [authorization])
    def get_family_details(self, request):
        try:
            get_datails = FamilyDetails.objects.filter(auth=request.GET["token"]["id"]).values('family_last_name','slogan')
            return Response(
                {"status": True, "data": get_datails}, status=status.HTTP_200_OK
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)
    
    @action(detail=False, methods=["POST"],permission_classes = [authorization])
    def add_details(self, request):
        try:
            family_last_name = request.data.get('family_last_name', None)
            slogan = request.data.get('slogan', None)
        
            auth_user_id = str(request.GET["token"]["id"])
            existing_record = FamilyDetails.objects.filter(auth_id=auth_user_id).first()
            if existing_record:
                existing_record.family_last_name = family_last_name
                existing_record.slogan = slogan
                existing_record.save()
                serializer = FamilyDetailsSerializer(existing_record)
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
            else:
                serializer = FamilyDetailsSerializer(data={'family_last_name': family_last_name, 'slogan': slogan, 'auth': auth_user_id})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(
                    {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
                )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)

    @action(detail=False, methods=["GET"],permission_classes = [authorization])
    def get_logo_symbols(self, request):
        try:
            data = LogoSymbol.objects.all().order_by('-created_at')
            serializer = LogoSymbolSerializer(data,many=True)
            data = [{"lable":"Are there any specific symbols or icons that hold significance for your family?",
                "labelDesc":"Here’s some samples",
                "data": serializer.data}]
            return Response(
                {
                "status": True,
                "data":data,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)
    
    @action(detail=False, methods=["GET"],permission_classes = [authorization])
    def get_logo_colours(self, request):
        try:
            data = LogoColor.objects.all().order_by('-created_at')
            serializer = LogoColorSerializer(data,many=True)
            data = [{"lable":"Do you have specific colors in mind for the logo?",
                "labelDesc":"Choose their top 3",
                "data": serializer.data}]
            return Response(
                {
                "status": True,
                "data":data,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=500)
        
    @action(detail=False, methods=["POST"],permission_classes = [authorization])
    def get_svgs(self, request):
        # try:
            requireFeild = ["family_last_name", "slogan", "colour_code", "svg_category_id"]
            validator = keyValidation(True, True, request.data, requireFeild)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            family_last_name = request.data["family_last_name"]
            slogan = request.data["slogan"]
            colour_code = request.data["colour_code"]
            svg_category_id = request.data["svg_category_id"]

            # Ensure colour_code is a string
            if not isinstance(colour_code, str):
                colour_code = str(colour_code)
            random.seed(42)
            # Fetch all LogoSvg objects for the given svg_category_id
            # id_list = ["e44c1abd-5484-4970-a211-f77b5af7ad3f","16d87af4-7685-486e-9882-0117b396c7b0","06f60343-8d5f-4295-baf6-965789a04104","22c6220f-b4f5-42bc-94c2-1901e1050833","24a8b4fd-eea5-4a4d-b996-7986ef3e950f","714b9f90-120d-4ade-8528-904d990d6c68","765c9579-4104-4a56-9a6b-b507d021d7c6"]
            all_svgs = LogoSvg.objects.filter(style__id=svg_category_id)
            # Shuffle the queryset randomly
            shuffled_svgs = list(all_svgs)
            random.shuffle(shuffled_svgs)
            selected_svgs = shuffled_svgs
            payload = {'family_last_name': family_last_name, 'slogan': slogan, 'colour_code': colour_code,
                    'svg_category_id': svg_category_id}
            serializer = LogoSvgSerializer(selected_svgs, many=True)
            message = {"status": True, "payload": payload, "data": []}  # Initialize 'data' as an empty list

            for svg_data in serializer.data:
                
                data = {'id': svg_data['id'],'logo':svg_data['logo'], 'height': '200', 'width': '200', 'viewBox': '0 0 313 190',
                        'text': family_last_name, 'slogan': slogan, 'paths': []}
                del svg_data['id']
                svg_tree = ET.fromstring(svg_data['svg_code'])
                path_elements = svg_tree.findall(".//{http://www.w3.org/2000/svg}path")
                text_elements = get_text_elements(svg_data['svg_code'],family_last_name,slogan)
                data['viewBox'] = svg_tree.attrib.get('viewBox', '0 0 200 200')
                colour_code_list = ast.literal_eval(colour_code)
                random.seed(42)
                selected_colour_code = random.choice(colour_code_list)
                for path in path_elements:
                    data['paths'].append({'d': path.get("d"), 'fill': selected_colour_code})

                # Append 'data' with the modified structure
                data['text_element'] = text_elements
                message['data'].append(data)

            # Return the modified message
            return Response(message, status=status.HTTP_200_OK)
        # except Exception as e:
        #     message = {"status": False}
        #     message.update(message=str(e)) if settings.DEBUG else message.update(
        #         message="Internal server error"
        #     )
        # return Response(message, status=500)
    
    @action(detail=False, methods=["POST"],permission_classes = [authorization])
    def add_svgs(self, request):
        requireFeild = ["logo", "style"]
        validator = keyValidation(True, True, request.data, requireFeild)
        if validator:
            return Response(validator, status=status.HTTP_400_BAD_REQUEST)

        logo = request.data.getlist('logo')
        style = request.data["style"]
        
        get_svg_symbol_obj = LogoSymbol.objects.filter(id = style).first()
        for i in range(len(logo)):
            data = LogoSvg(logo = logo[i],style = get_svg_symbol_obj)
            data.save()
        return Response(
                {
                "status": True,
                "message":"added successfully",
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=["POST"],permission_classes = [authorization])
    def add_svgs_category(self, request):
        requireFeild = ["logo", "style", "logo_svg"]
        validator = keyValidation(True, True, request.data, requireFeild)
        if validator:
            return Response(validator, status=status.HTTP_400_BAD_REQUEST)

        logo = request.data.getlist('logo')
        style = request.data["style"]
        logo_svg = request.data["logo_svg"]
        
        get_svg_symbol_obj = LogoSymbol.objects.filter(id = style).first()
        get_logo_svg_obj = LogoSvg.objects.filter(id = logo_svg).first()
        for i in range(len(logo)):
            data = RelatedSvg(logo = logo[i],style = get_svg_symbol_obj,logo_svg = get_logo_svg_obj)
            data.save()
            print("-------------",data.id)
        return Response(
                {
                "status": True,
                "message":"added successfully",
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=["POST"],permission_classes = [authorization])
    def get_svgs_category(self, request):
        try:
            requireFeild = ["family_last_name", "slogan", "colour_code", "svg_category_id","svg_id"]
            validator = keyValidation(True, True, request.data, requireFeild)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            family_last_name = request.data["family_last_name"]
            slogan = request.data["slogan"]
            colour_code = request.data["colour_code"]
            svg_category_id = request.data["svg_category_id"]
            svg_id = request.data["svg_id"]

            # Ensure colour_code is a string
            if not isinstance(colour_code, str):
                colour_code = str(colour_code)

            # Fetch all LogoSvg objects for the given svg_category_id
            all_svgs = RelatedSvg.objects.filter(style__id=svg_category_id,logo_svg__id = svg_id)

            # Shuffle the queryset randomly
            shuffled_svgs = list(all_svgs)
            random.shuffle(shuffled_svgs)

            selected_svgs = shuffled_svgs
            payload = {'family_last_name': family_last_name, 'slogan': slogan, 'colour_code': colour_code,
                    'svg_category_id': svg_category_id}
            serializer = RelatedSvgSerializer(selected_svgs, many=True)
            message = {"status": True, "payload": payload, "data": []}  # Initialize 'data' as an empty list

            for svg_data in serializer.data:
                
                data = {'id': svg_data['id'], 'height': '200', 'width': '200', 'viewBox': '0 0 313 190',
                        'text': family_last_name, 'slogan': slogan, 'paths': []}
                del svg_data['id']

                svg_tree = ET.fromstring(svg_data['svg_code'])
                path_elements = svg_tree.findall(".//{http://www.w3.org/2000/svg}path")
                text_elements = get_text_elements(svg_data['svg_code'],family_last_name,slogan)
                data['viewBox'] = svg_tree.attrib.get('viewBox', '0 0 200 200')
                colour_code_list = ast.literal_eval(colour_code)
                random.seed(42)
                selected_colour_code = random.choice(colour_code_list)
                for path in path_elements:
                    
                    data['paths'].append({'d': path.get("d"), 'fill': selected_colour_code})

                # Append 'data' with the modified structure
                data['text_element'] = text_elements
                message['data'].append(data)

            # Return the modified message
            return Response(message, status=status.HTTP_200_OK)
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
        return Response(message, status=500)

    @action(detail=False, methods=["POST"])
    def get_svgs_webview(self, request):
        try:
            requireFeild = ["family_last_name", "slogan", "colour_code", "svg_category_id",'url']
            validator = keyValidation(True, True, request.data, requireFeild)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            family_last_name = request.data["family_last_name"]
            slogan = request.data["slogan"]
            colour_code = request.data["colour_code"]
            svg_category_id = request.data["svg_category_id"]
            url = request.data["url"]

            svgs_data = list(LogoSvg.objects.filter(style__id=svg_category_id))
            svgs_data = random.sample(svgs_data,3)
            serializer = LogoSvgSerializer(svgs_data, many=True).data
            payload = {'family_last_name': family_last_name, 'slogan': slogan, 'colour_code': colour_code,
                    'svg_category_id': svg_category_id,"url":url}
            message = {"status": True, "payload": payload, "data": serializer} 
            
            return Response(message, status=status.HTTP_200_OK)
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
        return Response(message, status=500)
    
    @action(detail=False, methods=["POST"])
    def get_svgs_category_webview(self, request):
        try:
            requireFeild = ["family_last_name", "slogan", "colour_code", "svg_category_id","svg_id","url"]
            validator = keyValidation(True, True, request.data, requireFeild)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            family_last_name = request.data["family_last_name"]
            slogan = request.data["slogan"]
            colour_code = request.data["colour_code"]
            svg_category_id = request.data["svg_category_id"]
            svg_id = request.data["svg_id"]
            url = request.data["url"]
            
            all_svgs = RelatedSvg.objects.filter(style__id=svg_category_id,logo_svg__id = svg_id)

            serializer = RelatedSvgSerializer(all_svgs, many=True).data
            payload = {'family_last_name': family_last_name, 'slogan': slogan, 'colour_code': colour_code,
                    'svg_category_id': svg_category_id,"url":url}
            message = {"status": True, "payload": payload, "data": serializer}  # Initialize 'data' as an empty list
            return Response(message, status=status.HTTP_200_OK)
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
        return Response(message, status=500)

    @action(detail=False, methods=["POST"])
    def save_logo_webview(self, request):
        try:
            svg_id = request.data.get('svg_id')
            url = request.data["url"]
            logo = request.FILES['logo']
            
            token_id = request.GET.get('token') 
            family_obj = FamilyDetails.objects.get(auth__id=token_id['id'])
            logo_svg_obj = RelatedSvg.objects.get(id=svg_id)

            user_logo_obj = UserLogo(family=family_obj, logo=logo, logo_svg=logo_svg_obj)
            user_logo_obj.save()

            message = {"status": True, "message": "logo saved successfully","url":url}
            return Response(message, status=status.HTTP_200_OK)
        except Exception as e:
            message = {"status": False, "message": str(e)}
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_text_elements(svg_code,family_last_name,slogan):
    text_elements = []

    # Parse SVG code
    svg_tree = ET.fromstring(svg_code)
    
    # Find all text elements in the SVG
    text_nodes = svg_tree.findall(".//{http://www.w3.org/2000/svg}text")

    # Iterate through each text element
    for text_node in text_nodes:
        text_data = {}

        # Extract attributes
        text_data['transform'] = text_node.attrib.get('transform', '')
        text_data['style'] = text_node.attrib.get('style', '')
        text_data['fontSize'] = text_node.attrib.get('font-size', '')
        text_data['fontFamily'] = "BerkshireSwash-Regular"
        text_data['color'] = "#000000"
        
        # Extract text content
        text_data['content'] = text_node.text.strip() if text_node.text else ''

        # Append to the list
        print("len--------------------",len(text_elements))
        if len(text_elements) == 0:
            text_data['content'] = family_last_name
        if len(text_elements) == 1:
            text_data['content'] = slogan
        text_elements.append(text_data)

    return text_elements

