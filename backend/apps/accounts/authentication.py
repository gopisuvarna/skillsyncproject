"""JWT authentication with HTTP-only cookie extraction."""
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import jwt
from .models import User


class JWTCookieAuthentication(authentication.BaseAuthentication):
    """Extract JWT from HTTP-only cookie or Authorization header."""
    def authenticate(self, request):
        access_name = settings.COOKIE_CONFIG['ACCESS_COOKIE_NAME']
        token = request.COOKIES.get(access_name)
        if not token:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return None
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_CONFIG['ALGORITHM']],
            )
            user_id = payload.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token')
            user = User.objects.get(id=user_id, is_active=True)
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise exceptions.NotAuthenticated('Token expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')