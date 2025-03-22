from rest_framework.response import Response
from rest_framework import status
from .exception_handler import APIError


class APIResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        return Response(
            {"success": True, "message": message, "data": data, "errors": None},
            status=status_code,
        )

    @staticmethod
    def error(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        raise APIError(message=message, status_code=status_code)

    # Common HTTP Status responses
    @staticmethod
    def bad_request(message="Bad Request", errors=None):
        raise APIError(message=message, status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def unauthorized(message="Unauthorized"):
        raise APIError(message=message, status_code=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message="Forbidden"):
        raise APIError(message=message, status_code=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def not_found(message="Not Found"):
        raise APIError(message=message, status_code=status.HTTP_404_NOT_FOUND)
