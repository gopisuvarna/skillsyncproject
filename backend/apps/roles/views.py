# """Role listing view."""
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.db.models import Prefetch

# from .models import Role, RoleSkill
# from .serializers import RoleSerializer


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def list_roles(request):
#     roles = Role.objects.prefetch_related(
#         Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
#     ).all()
#     return Response(RoleSerializer(roles, many=True).data)


"""Role listing view — paginated."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch, Q

from .models import Role, RoleSkill
from .serializers import RoleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_roles(request):
    """
    Paginated role listing with optional search.

    Query params:
        page      (int, default 1)
        per_page  (int, default 20, max 50)
        q         (str) — search by role title
    """
    page     = max(1, int(request.query_params.get('page', 1)))
    per_page = min(int(request.query_params.get('per_page', 20)), 50)
    q        = request.query_params.get('q', '').strip()
    offset   = (page - 1) * per_page

    qs = Role.objects.prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    )

    if q:
        qs = qs.filter(title__icontains=q)

    total = qs.count()
    roles = qs[offset: offset + per_page]

    return Response({
        'total':    total,
        'page':     page,
        'per_page': per_page,
        'results':  RoleSerializer(roles, many=True).data,
    })

