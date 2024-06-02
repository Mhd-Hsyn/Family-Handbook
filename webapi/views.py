"""
Views for the Django application.
"""
import random
import ast
from uuid import UUID
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import status
from decouple import config
from django.conf import settings
from passlib.hash import django_pbkdf2_sha256 as handler
from core.helper import (
    keyValidation,
    exceptionhandler,
    generatedToken,
    checkemailforamt,
    passwordLengthValidator
)
from core.sendemail import sendotp
from core.permissions import (
    authorization,
    UserPermission
)
from api.models import *
from webapi.serializers import *
from .Useable import prompts
from .pagination import *
# from webapi.serializers import (
#     UserRegisterSerializer,
#     UserAllPdfSerializer,
#     UserCreatePdfSerializer,
# )

# Create your views here.


def index(request):
    return HttpResponse("<h1>Project family-handbook</h1>")



class UserAuthViewset(ModelViewSet):
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
            print(request.data)
            ser = UserRegisterSerializer(data=request.data)
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
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def login(self, request):
        try:
            email = request.data["email"]
            password = request.data["password"]

            user = Auth.objects.filter(email=email).first()
            
            if user and handler.verify(password, user.password):
                generate_auth = generatedToken(user, config("User_jwt_token"), 100, request)
                
                if generate_auth["status"]:
                    user.no_of_wrong_attempts = 0
                    user.save()
                    # fetch all pdf after login
                    fetch_all_pdfs = Pdf.objects.filter(user_id= user).order_by("-created_at")
                    if not fetch_all_pdfs.exists():
                        # if not any pdf then create pdf of user
                        Pdf.objects.create(user_id=user, name=user.full_name, font_style=3)
                        fetch_all_pdfs = Pdf.objects.filter(user_id= user)

                    all_pdf_ser= UserAllPdfSerializer(fetch_all_pdfs, many=True)
                    return Response(
                        {
                            "status": True,
                            "message": "Login SuccessFully",
                            "token": generate_auth["token"],
                            "data": generate_auth["payload"],
                            "all_pdf": all_pdf_ser.data
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(generate_auth)
            else:
                return Response(
                    {"status": False, "message": "Invalid Credential"}, status=401
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

                fetchuser = Auth.objects.filter(email=email).first()
                if fetchuser:
                    token = random.randrange(100000, 999999, 6)
                    fetchuser.otp = token
                    fetchuser.otp_count = 0
                    fetchuser.otp_status = True
                    fetchuser.save()
                    emailstatus = sendotp(email,token)
                    if emailstatus:
                        return Response(
                            {
                                "status": True,
                                "message": "Email send successfully",
                                "email": fetchuser.email,
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
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["POST"])
    def reset_password(self, request):
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
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Step No.1 Initializing PDF 
class UserPDF(APIView):
    """
    This Class is responsible of the PDF in User's Account for Family Handbook
    This PDF will store all 10 modules which are in the Family Handbook
    i.e Cover Pgae, Introduction, Family Bios, Vision and Mission Statement and e.t.c
    """
    permission_classes = [UserPermission]
    def get(self, request, format=None):
        """
        GET all pdf of the perticular User
        """
        try:
            user_id= request.auth["id"]
            user= Auth.objects.get(id= user_id)
            fetch_all_pdfs = Pdf.objects.filter(user_id= user).order_by("-created_at")
            if not fetch_all_pdfs.exists():
                Pdf.objects.create(user_id=user, name=user.full_name, font_style=3)
                fetch_all_pdfs = Pdf.objects.filter(user_id= user)
            
            paginator = PDFPagination()
            page = paginator.paginate_queryset(fetch_all_pdfs, request)
            all_pdf_ser= UserAllPdfSerializer(page, many=True)
            return paginator.get_paginated_response(all_pdf_ser.data)
        
        except (KeyError, TypeError):
             return Response(
                    {"status": False,"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ObjectDoesNotExist:
            return Response(
                    {"status": False,"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        """
        Initializing the new PDF in User's Account for Family Handbook
        """
        try:
            user_id= request.auth['id']
            required_fields= ['name', 'ip_address', 'font_style']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            user = Auth.objects.get(id= user_id)
            serializer= UserCreatePdfSerializer(data= request.data, context= {"user": user})
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True,"message": "PDF create successfully"},
                    status=status.HTTP_200_OK,
                )
            else:
                error_message = exceptionhandler(serializer)
                return Response(
                    {"status": False, "message": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        except (KeyError, TypeError):
            return Response(
                {"status": False,"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ObjectDoesNotExist:
            return Response(
                {"status": False, "message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            user_id= request.auth['id']
            print(user_id)
            required_fields= ['name', 'pdf_id']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_pdf= Pdf.objects.get(id= request.data.get("pdf_id"), user_id= user_id)
            fetch_pdf.name= request.data.get("name")
            fetch_pdf.save()
            return Response(
                    {"status": True,"message": "PDF updated successfully"},
                    status=status.HTTP_200_OK,
                )

        except (KeyError, TypeError):
            return Response(
                    {"status": False,"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ObjectDoesNotExist:
            return Response(
                {"status": False, "message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            

            

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request):
        """
        Delete the PDF of User's FamilyHandbook
        This will also delete the all modules which are linked with this PDF
        """
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id']
            validator = keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            pdf= Pdf.objects.get(id= request.GET.get("pdf_id"), user_id= user_id)
            
            pdf.delete()
            return Response(
                {"status": True, "message": "PDF delete Successfully"},
                status=status.HTTP_200_OK
            )
        except (KeyError, TypeError):
            return Response (
                {"status": False,"message": "Exception in Authorization"},
                status= status.HTTP_404_NOT_FOUND
            )
        
        except ObjectDoesNotExist:
            return Response(
                {"status": False, "message": "PDF not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Step 2. Information of all modules (completed or not completed) in perticular PDF
class PdfModuleInfo(APIView):
    permission_classes= [UserPermission]

    def get(self, request):
        """
        This APi is reponsible of the retreiving the User's Family Handbook 
        all modules Information (completed or not completed)
        CoverPage, Introduction, family_bios e.t.c 
        """
        try:
            user_id= request.auth['id']
            message= {"status": True ,"message": ""}
            required_field= ['pdf_id']
            validator= keyValidation(True, True, request.GET, required_field)
            if validator:
                return Response(validator, status= status.HTTP_400_BAD_REQUEST)
            
            pdf_id= request.GET.get("pdf_id")
            fetch_pdf= Pdf.objects.filter(id= pdf_id, user_id= user_id).first()
            if not fetch_pdf:
                message['status']= False
                message["message"]= "pdf not found for this user"
                return Response(message, status= status.HTTP_400_BAD_REQUEST)

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
                query= model.objects.filter(pdf_id= pdf_id).first()
                if query:
                    message[model.__name__]= query.is_finished
                else:
                    message[model.__name__]= 0
            
            message['message']= "All Modeules information"
            return Response (message, status= status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Module No 1 Cover Page
class CoverPageModuleViewset(ModelViewSet):
    """
    Module No 1. of FHB Web Module  ( Cover Page )
    User Authorization is needed, using UserPermission class
    """
    permission_classes = [UserPermission]

    @action(detail=False, methods=['POST'])
    def upload_image(self, request):
        """
        Upload Family Image in Cover Page Module
        """
        try:
            user_id= request.auth['id']
            required_field= ['pdf_id', 'image']
            validator= keyValidation(True, True, request.data, required_field)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_coverpage = CoverPage.objects.filter(pdf_id= request.data['pdf_id'], pdf_id__user_id= user_id).first()
            serializer= UploadCoverPageImageSerializer(instance=fetch_coverpage , data = request.data, context= {"user_id": user_id})
            action_message = "Image Updated Successfully" if fetch_coverpage else "Image Added Successfully"
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "message": action_message}, 
                    status= status.HTTP_200_OK
                )
            else :
                error_message = exceptionhandler(serializer)
                return Response(
                    {"status": False, "message": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def add_coverpage(self, request):
        """
        Add Information and Data on the Cover Page of the Family Handbook
        """
        try:
            user_id = request.auth.get('id')
            required_fields = ['pdf_id']

            # Validate required fields
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            pdf_id = request.data.get('pdf_id')
            fetch_coverpage = CoverPage.objects.filter(pdf_id=pdf_id, pdf_id__user_id=user_id).first()
            
            # If cover page exists, update it; otherwise, create a new one
            serializer = PDFCoverPageSerializer(instance=fetch_coverpage, data=request.data, context={"user_id": user_id})
            action_message = "Cover Page Updated Successfully" if fetch_coverpage else "Cover Page Added Successfully"
            
            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "message": action_message}, status=status.HTTP_200_OK)
            else:
                error_message = exceptionhandler(serializer)
                return Response({"status": False, "message": error_message}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError:
            return Response({'status': False, 'message': 'Authorization header missing or invalid'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            error_message = "Internal server error" if not settings.DEBUG else str(e)
            return Response({'status': False, 'message': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_coverpage(self, request):
        """
        GET coverpage of the PDF of the user's Family Handbook
        """
        try:
            user_id = request.auth.get('id')
            pdf_id = request.GET.get("pdf_id", None)
            if pdf_id is None:
                return Response(
                    {'status': False, 'message': 'pdf_id required'}, 
                    status= status.HTTP_400_BAD_REQUEST
                )
            # Fetch CoverPage object
            fetch_coverpage = CoverPage.objects.get(pdf_id=pdf_id, pdf_id__user_id=user_id)
            serializer= GetCoverPageSerializer(fetch_coverpage).data
            return Response(
                {'status': True, **serializer},
                status=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return Response (
                {'status': False, 'message': "Cover page not found for this user and PDF"},
                status=status.HTTP_404_NOT_FOUND
            )
        except KeyError:
            return Response(
                {'status': False, 'message': 'Authorization header missing or invalid'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Module No 2 INTRODUCTION of Web Module of FHB
class IntroductionModuleViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['GET'])
    def get_intro(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.GET.get("pdf_id", None)
            if not pdf_id:
                return  Response(
                    {'status': False, "message": "pdf_id must be required"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_intro_page= IntroductionPage.objects.filter(
                pdf_id= pdf_id,
                pdf_id__user_id= user_id
            ).first()
            if not fetch_intro_page:
                return Response(
                    {"status": False, "message": "PDF not found for that user"},
                    status= status.HTTP_200_OK
                )
            ser_data = GetIntroPageSer(fetch_intro_page).data
            return Response({"status": True, **ser_data}, status=200)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # chat-gpt implemented
    @action(detail=False, methods=['POST'])
    def add_intro(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id', 'beginning_letter', 'tone_used', 'character_list']
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)

            fetch_pdf= Pdf.objects.filter(id= request.data.get('pdf_id'), user_id=user_id).first()
            if not fetch_pdf:
                return Response(
                    {"status": False, "message": "PDF not found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                    )
            fetch_intro= IntroductionPage.objects.filter(pdf_id= fetch_pdf).first()
            intro_ser= ADDIntroPageSerializer(instance=fetch_intro, data=request.data, context= {'user_id': user_id})
            message= "Introduction Updated successfully" if fetch_intro else "Introduction Added successfully"
            if intro_ser.is_valid():
                intro_ser.save()
                return Response({'status': True, "message": message, "note": intro_ser.validated_data['note']})

            else:
                error_message = exceptionhandler(intro_ser)
                return Response({"status": False, "message": error_message}, status=status.HTTP_400_BAD_REQUEST)
                
        except KeyError:
            return Response(
                {'status': False, 'message': 'Authorization header missing or invalid'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    # @action(detail=False, methods=['POST'])
    # def writting_assistant(self, request):
    #     try:
    #         user= request.auth['id']
    #         pdf_id = request.data.get("pdf_id", None)
    #         note = request.data.get("note", None)
    #         if not pdf_id and not note:
    #             return Response({"status": False, "message": "pdf_id and note both required ..."}, status=status.HTTP_400_BAD_REQUEST)
            
    #         fetch_intro= IntroductionPage.objects.filter(pdf_id= pdf_id, pdf_id__user_id= user).first()
    #         if not fetch_intro:
    #             return Response({"status": False, "message": "pdf not found ..."}, status=status.HTTP_400_BAD_REQUEST)
            
    #         characters_list= fetch_intro.characters_list
    #         characters_list= ast.literal_eval(characters_list)
    #         characters_list = ', '.join(str(character) for character in characters_list)

    #         rephase_note = prompts.writting_assis_IntroPage(
    #             note=note,
    #             chatacters_list=characters_list,
    #             starting=fetch_intro.beginning_letter,
    #             tone= fetch_intro.tone_used
    #             )
    #         fetch_intro.note = rephase_note
    #         fetch_intro.save()
    #         return Response({'status': True, 'note': rephase_note}, status= status.HTTP_200_OK)
        
    #     except (SyntaxError, ValueError):
    #         return Response({"status": False, "message": "Invalid characters list format in database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #     except Exception as e:
    #         message = {"status": False}
    #         message.update(message=str(e)) if settings.DEBUG else message.update(
    #             message="Internal server error"
    #         )
    #         return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # chat-gpt implemented
    @action(detail=False, methods=['POST'])
    def writting_assistant(self, request):
        try:
            note = request.data.get("note", None)
            if not note:
                return Response({"status": False, "message": "note is required ..."}, status=status.HTTP_400_BAD_REQUEST)
            
            rephase_note = prompts.writting_assis_IntroPage(
                note=note,
                )
            return Response({'status': True, 'note': rephase_note}, status= status.HTTP_200_OK)
        
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def save_intro_note(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.data.get('pdf_id', None)
            note = request.data.get('note', None)
            if not pdf_id and not note:
                return Response(
                    {"status": False, "message": "pdf_id and note must be required ..."},
                    status=status.HTTP_400_BAD_REQUEST
                    )

            fetch_into_page= IntroductionPage.objects.filter(
                pdf_id= pdf_id,
                pdf_id__user_id= user_id
            ).first()
            if not fetch_into_page:
                return Response(
                    {"status": False, "message": "PDF not found for this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            save_intro_ser= SaveInroNoteSerializer(fetch_into_page, data={"note": note})
            if save_intro_ser.is_valid():
                save_intro_ser.save()
                return Response(
                    {"status": True, "message": "note save successfully"},
                    status=status.HTTP_200_OK
                    )
            else: 
                exception= exceptionhandler(save_intro_ser)
                return Response(
                    {"status": False, "message": exception},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




#########################################################################################
# Module No.3   FAMILY MEMBERS


class FamilyMembersModelViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['POST'])
    def add_parents(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.data.get('pdf_id', None)
            required_fields= ["pdf_id", "full_name", "dob", "email"]
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            # fetch pdf and check is this pdf is associate with this, same user 
            fetch_pdf= Pdf.objects.filter(id= pdf_id,user_id= user_id).first()
            if not fetch_pdf:
                return Response(
                    {"status": False, "message": "pdf not found with this user ..."},
                    status=status.HTTP_404_NOT_FOUND
                    )

            fetch_family_bios= family_bios.objects.filter(pdf_id= pdf_id).first()
            if not fetch_family_bios:
                fetch_family_bios= family_bios.objects.create(pdf_id= fetch_pdf, is_begin= "1")

            add_parent_ser= AddParentMemberSerializer(data=request.data, context= {"family_bios_id": fetch_family_bios})
            if add_parent_ser.is_valid():
                add_parent_ser.save()
                return Response(
                    {"status": True, "message": "parent addded successfully"},
                    status=status.HTTP_201_CREATED
                    )
            else:
                exception= exceptionhandler(add_parent_ser)
                return Response(
                    {"status": False, "message": exception},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @action(detail=False, methods=['GET'])
    def get_parents(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.data.get('pdf_id', None)
            required_fields= ["pdf_id"]
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            # fetch pdf and check is this pdf is associate with this, same user 
            fetch_pdf= Pdf.objects.filter(id= pdf_id,user_id= user_id).first()
            if not fetch_pdf:
                return Response(
                    {"status": False, "message": "pdf not found with this user ..."},
                    status=status.HTTP_404_NOT_FOUND
                    )
            
            # verify if this pdf is associate with same user 
            fetch_family_bios= family_bios.objects.filter(pdf_id= pdf_id, pdf_id__user_id__id= user_id ).first()
            if not fetch_family_bios:
                return Response ({"status": False, "message": "No parents"}, status=400)
            
            fetch_parents= parent_members.objects.filter(family_bios_id= fetch_family_bios)
            parent_ser= GetParentMemberSerializer(fetch_parents, many=True)
            return Response(
                {"status": True, "parent_data": parent_ser.data},
                status=status.HTTP_200_OK
                )
            
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail= False, methods= ['PUT'])
    def edit_parent(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['parent_id', "full_name", "dob", "email"]
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            parent_id= request.data.get("parent_id")

            # verify if this pdf is associate with same user 
            fetch_parent= parent_members.objects.filter(id= parent_id, family_bios_id__pdf_id__user_id__id= user_id).first()
            if not fetch_parent:
                return Response ({"status": False, "message": "No parents found"}, status=400)

            update_parent_ser= UpdateParentMemberSerializer(instance=fetch_parent, data=request.data)
            if update_parent_ser.is_valid():
                update_parent_ser.save()
                return Response(
                    {"status": True, "message": "parent Updated successfully"},
                    status=status.HTTP_200_OK
                    )
            else:
                exception= exceptionhandler(update_parent_ser)
                return Response(
                    {"status": False, "message": exception},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(detail= False, methods= ['DELETE'])
    def delete_parent(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['parent_id']
            validator= keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            parent_id= request.GET.get("parent_id")

            # verify if this pdf is associate with same user 
            fetch_parent= parent_members.objects.filter(id= parent_id, family_bios_id__pdf_id__user_id__id= user_id).first()
            if not fetch_parent:
                return Response ({"status": False, "message": "No parents found"}, status=400)

            fetch_parent.delete()
            return Response(
                {"status": True, "message": "parent Deleted successfully"},
                status=status.HTTP_200_OK
                )

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




#########################################################################################
# Module No.4   CORE VALUE
class CoreValueModuleViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=["POST"])
    def writting_assistant(self, request):
        try:
            required_fields= ['value_one', 'value_two', 'value_three', 'value_four', 'value_five']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
    
            data= request.data
            selected_words = ','.join([data[field] for field in required_fields])
            note= prompts.getCoreValueStatement(selected_words)
            return Response({'status': True, 'note': note}, status= status.HTTP_200_OK)
        
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def add_corevalue(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id', 'value_one', 'value_two', 'value_three', 'value_four', 'value_five', 'note']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_pdf= Pdf.objects.filter(id= request.data.get('pdf_id'), user_id = user_id).first()
            if not fetch_pdf:
                return Response(
                    {"status": False, "message": "PDF not found for this user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                    )
            fetch_coreval= CoreValues.objects.filter(pdf_id= fetch_pdf).first()
            data = request.data
            data['is_finished'] = 1
            core_val_ser = CoreValueSer(fetch_coreval, data=data)
            if core_val_ser.is_valid():
                core_val_ser.save()
                message= "Core Values Updated Successfully" if fetch_coreval else "Core Values Added Successfully"
                return Response(
                    {'status': True, "message": message},
                    status= status.HTTP_200_OK
                )
            else:
                exception= exceptionhandler(core_val_ser)
                return Response(
                    {'status': False, "message": exception},
                    status= status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods= ['GET'])
    def get_core_val(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.GET.get("pdf_id", None)
            if not pdf_id:
                return Response(
                    {'status':False, "message": "pdf_id must be required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            fetch_core_val= CoreValues.objects.filter(
                pdf_id=pdf_id,
                pdf_id__user_id__id = user_id
            ).first()
            if fetch_core_val:
                ser= CoreValueSer(fetch_core_val)
                return Response({'status': True, **ser.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, "data": "PDF not found with this user"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Module No. 05    VisionStatements
class VisionStatementModuleViewset(ModelViewSet):
    permission_classes= [UserPermission]
    
    @action(detail=False, methods=["POST"])
    def writting_assistant(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id','statements']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
    
            fetch_pdf= Pdf.objects.filter(id = request.data.get("pdf_id"), user_id= user_id).first()
            if not fetch_pdf:
                return Response({'status': False, "message": "PDF not found with this user"}, status=status.HTTP_400_BAD_REQUEST)
            
            statements= request.data.get("statements")
            fetch_Coreval= CoreValues.objects.filter(pdf_id= fetch_pdf).first()
            if fetch_Coreval:
                values= ['value_one', 'value_two', 'value_three', 'value_four', 'value_five']
                selected_words= ", ".join([getattr(fetch_Coreval, value) for value in values])
                coreval_stat= getattr(fetch_Coreval, "note")

                vision_statement= prompts.vision_statement_with_core_values(selected_words, coreval_stat, statements)
                return Response({'status': True, 'note': vision_statement}, status= status.HTTP_200_OK)
            
            else:
                vision_statement= prompts.simple_vision_statement(statements)
                return Response({'status': True, 'note': vision_statement}, status= status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_vision_stat(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.GET.get("pdf_id")
            if not pdf_id:
                return Response (
                    {"status": False, "message": "PDF not found with this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_vision_stat= VisionStatements.objects.filter(
                pdf_id= pdf_id,
                pdf_id__user_id= user_id
            ).first()
            if fetch_vision_stat:
                vision_ser = GETVissionStatSerializer(fetch_vision_stat).data
                return Response ({'status': True, **vision_ser}, status= status.HTTP_200_OK)
            else:
                return Response({'status': False, "data": "PDF not found with this user"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['POST'])
    def add_vision_stat(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id', 'note', 'heading']
            validator= keyValidation(True,False, request.data, required_fields )
            if validator:
                return Response(validator, status= status.HTTP_400_BAD_REQUEST)

            fetch_pdf= Pdf.objects.filter(id= request.data.get('pdf_id'), user_id= user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            
            fetch_vision= VisionStatements.objects.filter(
                pdf_id= fetch_pdf
            ).first()
            data=request.data
            data['is_finished']= 1
            vision_ser= VissionStatSerializer(fetch_vision, data=data)
            if vision_ser.is_valid():
                vision_ser.save()
                message= "Vission statement Updated Successfully" if fetch_vision else "Vision Statement Added Successfully"
                return Response({'status': True, "message": message}, status=status.HTTP_200_OK)
            else:
                exception= exceptionhandler(vision_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Module No. 06    Mission Statements
class MissionStatementModuleViewset(ModelViewSet):
    permission_classes= [UserPermission]
    
    @action(detail=False, methods=["POST"]) ##################################################
    def writting_assistant(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id','statements']
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
    
            fetch_pdf= Pdf.objects.filter(id = request.data.get("pdf_id"), user_id= user_id).first()
            if not fetch_pdf:
                return Response({'status': False, "message": "PDF not found with this user"}, status=status.HTTP_400_BAD_REQUEST)
            
            statements= request.data.get("statements")
            fetch_Coreval= CoreValues.objects.filter(pdf_id= fetch_pdf).first()
            if fetch_Coreval:
                values= ['value_one', 'value_two', 'value_three', 'value_four', 'value_five']
                selected_words= ", ".join([getattr(fetch_Coreval, value) for value in values])
                coreval_stat= getattr(fetch_Coreval, "note")

                mission_statement= prompts.mission_statement_with_core_values(selected_words, coreval_stat, statements)
                return Response({'status': True, 'note': mission_statement}, status= status.HTTP_200_OK)
            
            else:
                mission_statement= prompts.simple_mission_statement(statements)
                return Response({'status': True, 'note': mission_statement}, status= status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_mission_stat(self, request):
        try:
            user_id= request.auth['id']
            pdf_id= request.GET.get("pdf_id")
            if not pdf_id:
                return Response (
                    {"status": False, "message": "PDF not found with this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_mission_stat= MissionStatements.objects.filter(
                pdf_id= pdf_id,
                pdf_id__user_id= user_id
            ).first()
            if fetch_mission_stat:
                mission_ser = GETMissionStatSerializer(fetch_mission_stat).data
                return Response ({'status': True, **mission_ser}, status= status.HTTP_200_OK)
            else:
                return Response({'status': False, "data": "PDF not found with this user"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['POST'])
    def add_mission_stat(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id', 'note', 'heading']
            validator= keyValidation(True,False, request.data, required_fields )
            if validator:
                return Response(validator, status= status.HTTP_400_BAD_REQUEST)

            fetch_pdf= Pdf.objects.filter(id= request.data.get('pdf_id'), user_id= user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            
            fetch_vision= MissionStatements.objects.filter(
                pdf_id= fetch_pdf
            ).first()
            data=request.data
            data['is_finished']= 1
            vision_ser= MissionStatSerializer(fetch_vision, data=data)
            if vision_ser.is_valid():
                vision_ser.save()
                message= "Mission statement Updated Successfully" if fetch_vision else "Mission Statement Added Successfully"
                return Response({'status': True, "message": message}, status=status.HTTP_200_OK)
            else:
                exception= exceptionhandler(vision_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Module No. 7 Code of Conduct
class CodeOfConductModelViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['POST'])
    def add_values(self, request):
        try:
            user_id= request.auth['id']
            required_fields = ['pdf_id','statement_one']
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(
                    {**validator, "note": "pdf_id and statement_one must be filled"}, 
                    status=status.HTTP_400_BAD_REQUEST
                    )
            
            pdf_id= request.data.get("pdf_id")
            fetch_pdf= Pdf.objects.filter(id= pdf_id, user_id = user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_coc= CodeOfConducts.objects.filter(pdf_id= fetch_pdf).first()
            coc_ser= AddCodeOfConductSer(fetch_coc, data= request.data)
            if coc_ser.is_valid():
                coc_ser.validated_data['is_finished']= 1
                coc_ser.save()
                message= f"Successfully Updated Code of Conduct for pdf {pdf_id}" if fetch_coc else f"Successfully Added Code of Conduct for pdf {pdf_id}"
                code_status= status.HTTP_200_OK if fetch_coc else status.HTTP_201_CREATED
                return Response (
                    {'status': True, "message": message},
                    status= code_status
                )
            else:
                exception= exceptionhandler(coc_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_values(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id']
            validator= keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_coc= CodeOfConducts.objects.filter(
                pdf_id=request.GET.get("pdf_id"),
                pdf_id__user_id= user_id
            ).first()
            if not fetch_coc:
                return Response({"status": False, "message": "pdf not found"}, status=status.HTTP_400_BAD_REQUEST)
            coc_ser= GetCodeOfConductSer(fetch_coc).data
            return Response({"status": True, **coc_ser}, status=status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Module No. 8      Family Media Aggrement
class FamilyMediaAggrementModelViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['POST'])
    def add_values(self, request):
        try:
            user_id= request.auth['id']
            required_fields = ['pdf_id','statement_one']
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(
                    {**validator, "note": "pdf_id and statement_one must be filled"}, 
                    status=status.HTTP_400_BAD_REQUEST
                    )
            
            pdf_id= request.data.get("pdf_id")
            fetch_pdf= Pdf.objects.filter(id= pdf_id, user_id = user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_fma= FamilyMediaAgreements.objects.filter(pdf_id= fetch_pdf).first()
            fma_ser= AddFamilyMediaAggrementSerializer(fetch_fma, data= request.data)
            if fma_ser.is_valid():
                fma_ser.validated_data['is_finished']= 1
                fma_ser.save()
                message= f"Successfully Updated Family Media Aggrement for pdf {pdf_id}" if fetch_fma else f"Successfully Added Family Media Aggrement for pdf {pdf_id}"
                code_status= status.HTTP_200_OK if fetch_fma else status.HTTP_201_CREATED
                return Response (
                    {'status': True, "message": message},
                    status= code_status
                )
            else:
                exception= exceptionhandler(fma_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_values(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id']
            validator= keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_fma= FamilyMediaAgreements.objects.filter(
                pdf_id=request.GET.get("pdf_id"),
                pdf_id__user_id= user_id
            ).first()
            if not fetch_fma:
                return Response({"status": False, "message": "pdf not found"}, status=status.HTTP_400_BAD_REQUEST)
            fma_ser= GetAddFamilyMediaAggrementSerializer(fetch_fma).data
            return Response({"status": True, **fma_ser}, status=status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Module No. 9      Family Constitution
class FamilyConstitutionModelViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['POST'])
    def add_constituition(self, request):
        try:
            user_id= request.auth['id']
            required_fields = ['pdf_id','note']
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            pdf_id= request.data.get("pdf_id")
            fetch_pdf= Pdf.objects.filter(id= pdf_id, user_id = user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_fc= FamilyConstitutions.objects.filter(pdf_id= fetch_pdf).first()
            fc_ser= AddFamilyConstitutionSerializer(fetch_fc, data= request.data)
            if fc_ser.is_valid():
                fc_ser.validated_data['is_finished']= 1
                fc_ser.save()
                message= f"Successfully Updated Family Constitution for pdf {pdf_id}" if fetch_fc else f"Successfully Added Family Constitution for pdf {pdf_id}"
                code_status= status.HTTP_200_OK if fetch_fc else status.HTTP_201_CREATED
                return Response (
                    {'status': True, "message": message},
                    status= code_status
                )
            else:
                exception= exceptionhandler(fc_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_values(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id']
            validator= keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_fc= FamilyConstitutions.objects.filter(
                pdf_id=request.GET.get("pdf_id"),
                pdf_id__user_id= user_id
            ).first()
            if not fetch_fc:
                return Response({"status": False, "message": "pdf not found"}, status=status.HTTP_400_BAD_REQUEST)
            fc_ser= GetFamilyConstitutionSerializer(fetch_fc).data
            return Response({"status": True, **fc_ser}, status=status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Module No. 10      Family Book Summary
class FamilyBookSummaryModelViewset(ModelViewSet):
    permission_classes= [UserPermission]

    @action(detail=False, methods=['POST'])
    def add_summary(self, request):
        try:
            user_id= request.auth['id']
            required_fields = ['pdf_id','note']
            validator= keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            pdf_id= request.data.get("pdf_id")
            fetch_pdf= Pdf.objects.filter(id= pdf_id, user_id = user_id).first()
            if not fetch_pdf:
                return Response (
                    {'status': False, "message": "PDF not found for this user"},
                    status= status.HTTP_400_BAD_REQUEST
                )
            fetch_summary= Summary.objects.filter(pdf_id= fetch_pdf).first()
            summary_ser= AddFamilyBookSummarySerializer(fetch_summary, data= request.data)
            if summary_ser.is_valid():
                summary_ser.validated_data['is_finished']= 1
                summary_ser.save()
                message= f"Successfully Updated Summary for pdf {pdf_id}" if fetch_summary else f"Successfully Added Summary for pdf {pdf_id}"
                code_status= status.HTTP_200_OK if fetch_summary else status.HTTP_201_CREATED
                return Response (
                    {'status': True, "message": message},
                    status= code_status
                )
            else:
                exception= exceptionhandler(summary_ser)
                return Response ({'status': False, "message": exception}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_summary(self, request):
        try:
            user_id= request.auth['id']
            required_fields= ['pdf_id']
            validator= keyValidation(True, True, request.GET, required_fields)
            if validator:
                return Response(validator, status=status.HTTP_400_BAD_REQUEST)
            
            fetch_summary= Summary.objects.filter(
                pdf_id=request.GET.get("pdf_id"),
                pdf_id__user_id= user_id
            ).first()
            if not fetch_summary:
                return Response({"status": False, "message": "pdf not found"}, status=status.HTTP_400_BAD_REQUEST)
            summary_ser= GetFamilyBookSummarySerializer(fetch_summary).data
            return Response({"status": True, **summary_ser}, status=status.HTTP_200_OK)

        except Exception as e:
            message = {"status": False}
            message.update(message=str(e)) if settings.DEBUG else message.update(
                message="Internal server error"
            )
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
