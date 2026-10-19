"""
backend/api/views.py
Health-check view — the only endpoint for W0a.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    """GET /api/health/ → {"status": "ok"}"""
    return Response({"status": "ok"})
