from django.shortcuts import render

# Create your views here.
from rest_framework.views import exception_handler
from rest_framework.decorators import api_view
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "status": "error",
            "message": response.data.get("detail", "Ocurrió un error inesperado en el servidor"),
            "data": None
        }

    return response

#Helthcheck endpoint
@api_view(['GET'])
def healthcheck(request):
    return Response({"status": "ok"})