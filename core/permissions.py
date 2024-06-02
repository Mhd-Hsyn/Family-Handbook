from rest_framework import permissions
from rest_framework.exceptions import APIException
from rest_framework.exceptions import AuthenticationFailed
from decouple import config
from api.models import WhitelistToken, Auth
import jwt


class authorization(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            token_catch = request.META["HTTP_AUTHORIZATION"][7:]
            request.GET._mutable = True
            my_token = jwt.decode(
                token_catch, config("User_jwt_token"), algorithms=["HS256"]
            )
            request.GET["token"] = my_token
            # whitelistToken.objects.get(user=my_token["id"], token=token_catch)
            return True

        except:

            # return True
            raise NeedLogin()


class NeedLogin(APIException):
    status_code = 401
    default_detail = {"status": False, "message": "Unauthorized"}
    default_code = "not_authenticated"



class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            auth_token = request.META["HTTP_AUTHORIZATION"][7:]
            decode_token = jwt.decode(auth_token, config('User_jwt_token'), "HS256")
            whitelist = WhitelistToken.objects.filter(
                auth =  decode_token['id'],
                token = auth_token,
                auth__role__value= "user"
                ).first()
            if not whitelist:
                raise AuthenticationFailed(
                    {"status": False, "message": "Not Authorize User"}
                )
            request.auth = decode_token
            return True
        except AuthenticationFailed as af:
            raise af
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed({"status": False,"error":"Session Expired !!"})
        except jwt.DecodeError:
            raise AuthenticationFailed({"status": False,"error":"Invalid token"})
        except Exception as e:
            raise AuthenticationFailed({"status": False,"error":"Need Login", "exception": e})