"""
Views for the Django application.
"""
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from decouple import config
from django.conf import settings
from .models import (
    FamilyParentRegisterationDetail, 
    FamilyMemberRegisterationDetail, 
    FamilyRelationship
)
from api.models import (
    Auth,
    )
from .serializers import (
    FamilyRegisterSerializer,
    MemberSerializer,
    MultipleMemberSerializer,
    AuthSerializer,
    SignupSerializer
)
from core.permissions import authorization
from core.helper import (
    keyValidation,
    exceptionhandler,
    )

from .serializers import FamilyParentRegisterationDetailSerializer, FamilyMemberRegisterationDetailSerializer


# Create your views here.
def index(request):
    return HttpResponse("<h1>Project Family Handbook --Family Registeration</h1>")



class RegisterationViewset(ModelViewSet):

    @action(detail=False, methods=["POST"], permission_classes = [authorization])
    def head(self, request):
        try:
            required_fields = ["family_role", "name", "birth_city", "current_city" , "date_of_birth", "profession", "vision", "mission", "goals", "picture"]
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(
                    {"status": False, "message": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            auth_user_id = str(request.GET["token"]["id"])
            auth = Auth.objects.filter(id=auth_user_id).first()
        
            
            serializer = FamilyRegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(auth=auth)              

                return Response(
                    {"status": True, "message": "Added successfully"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                error_message = exceptionhandler(serializer)
                return Response(
                    {"status": False, "message": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
 

    @action(detail=False, methods=["POST"], permission_classes=[authorization])
    def add_family_member(self, request):
        try:
            serializer = MultipleMemberSerializer(data=request.data)

            if serializer.is_valid():
                members_data = serializer.validated_data['members']
                added_members = []
                auth_user_id = str(request.GET.get("token", {}).get("id"))

                # Fetch the authenticated parent
                auth_parent = FamilyParentRegisterationDetail.objects.filter(auth=auth_user_id).first()

                if auth_parent:
                    # Create or get the FamilyRelationship instance
                    relationship, created = FamilyRelationship.objects.get_or_create(parent=auth_parent)

                    for member_data in members_data:
                        member_serializer = MemberSerializer(data=member_data)
                        if member_serializer.is_valid():
                            member = member_serializer.save()
                            relationship.members.add(member)
                            added_members.append(member)
                        else:
                            return Response(
                                {"status": False, "message": member_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                    # Generate link for the member with parent id
                    link = config('link') + "?join=" + str(relationship.id)

                    return Response(
                        {"status": True, "message": "Members added successfully", "link": link},
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {"status": False, "message": "Authenticated parent not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {"status": False, "message": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=False, methods=["GET"])
    def get_family_member(self, request):
        try:
            required_fields = ["link"]
            link = request.data.get("link")
            
            # Validate required fields
            validator = keyValidation(True, True, request.data, required_fields)
            if validator:
                return Response(
                    {"status": False, "message": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate link
            validate_link = FamilyRelationship.objects.filter(id=link).first()
            if not validate_link:
                return Response(
                    {"status": False, "message": "Invalid link"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Get members of the validated link
            members = validate_link.members.all()
            member_serializer = MemberSerializer(members, many=True)

            return Response(
                {"status": True, "members": member_serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    #member signup in which member's email, password and other details are passed
    @action(detail=False, methods=["POST"])
    def member_signup(self, request):
        required_fields = ["email", "password", "family_role", "name", "birth_city", "current_city", "date_of_birth", "profession", "picture"]
        
        # Extract only required fields from request data
        data = {field: request.data.get(field) for field in required_fields}
        
        # Validate if all required fields are present
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return Response(
                {"status": False, "message": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize data for FamilyMemberRegisterationDetail
        serializer = SignupSerializer(data=data)
        
        if serializer.is_valid():
            try:
                # Query FamilyMemberRegisterationDetail for the family_role and name
                member_detail = FamilyMemberRegisterationDetail.objects.get(family_role=data.get("family_role"), name=data.get("name"))

                # Update the member's details
                serializer.update(member_detail, data)
                
                return Response(
                    {"status": True, "message": "Account updated successfully"},
                    status=status.HTTP_200_OK,
                )
            except FamilyMemberRegisterationDetail.DoesNotExist:
                return Response(
                    {"status": False, "message": "Member not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            error_message = serializer.errors
            return Response(
                {"status": False, "message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )


    ##registeration details get of parents and members  
    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def details(self, request):
        try:
            token = request.GET["token"]["id"]
            auth_instance = Auth.objects.get(id=token)
        except (Auth.DoesNotExist, ValueError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        parent_details = FamilyParentRegisterationDetail.objects.filter(auth=auth_instance).first()
        member_details = FamilyMemberRegisterationDetail.objects.filter(auth=auth_instance).first()

        if parent_details:
            parent_serializer = FamilyParentRegisterationDetailSerializer(parent_details)
            return Response(parent_serializer.data, status=status.HTTP_200_OK)
        elif member_details:
            member_serializer = FamilyMemberRegisterationDetailSerializer(member_details)
            return Response(member_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No registration details found for the provided token'}, status=status.HTTP_404_NOT_FOUND)


    ##registeration details update of parents and members  
    @action(detail=False, methods=["POST"], permission_classes=[authorization])
    def update_details(self, request):
        try:
            token = request.GET["token"]["id"]
            auth_instance = Auth.objects.get(id=token)
        except (Auth.DoesNotExist, ValueError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        parent_details = FamilyParentRegisterationDetail.objects.filter(auth=auth_instance).first()
        member_details = FamilyMemberRegisterationDetail.objects.filter(auth=auth_instance).first()

        if parent_details:
            parent_serializer = FamilyParentRegisterationDetailSerializer(parent_details, data=request.data)
            if parent_serializer.is_valid():
                parent_serializer.save()
                return Response(parent_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(parent_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif member_details:
            member_serializer = FamilyMemberRegisterationDetailSerializer(member_details, data=request.data)
            if member_serializer.is_valid():
                member_serializer.save()
                return Response(member_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No registration details found for the provided token'}, status=status.HTTP_404_NOT_FOUND)



    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def details(self, request):
        try:
            token = request.GET["token"]["id"]
            auth_instance = Auth.objects.get(id=token)
        except (Auth.DoesNotExist, ValueError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        parent_details = FamilyParentRegisterationDetail.objects.filter(auth=auth_instance).first()
        member_details = FamilyMemberRegisterationDetail.objects.filter(auth=auth_instance).first()

        if parent_details:
            parent_serializer = FamilyParentRegisterationDetailSerializer(parent_details)
            return Response(parent_serializer.data, status=status.HTTP_200_OK)
        elif member_details:
            member_serializer = FamilyMemberRegisterationDetailSerializer(member_details)
            return Response(member_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No registration details found for the provided token'}, status=status.HTTP_404_NOT_FOUND)





