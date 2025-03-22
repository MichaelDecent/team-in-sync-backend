from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class APIError(APIException):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.status_code = status_code
        self.detail = message


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        message = response.data.get("detail", None) if isinstance(exc, APIException) else "An error occurred"
        response.data = {
            "success": False,
            "message": message,
            "data": None,
            "errors": response.data,
        }

    return response
