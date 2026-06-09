from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "status": "error",
            "message": response.data.get(
                "detail",
                "Ocurrió un error inesperado en el servidor"
            ),
            "data": None
        }

    return response


@api_view(["GET", "HEAD"])
@permission_classes([AllowAny])
def healthcheck(request):
    return Response(
        {
            "Status": "Ok",
            "Code": 200,
        },
        status=200
    )
