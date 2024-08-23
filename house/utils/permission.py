from rest_framework.permissions import BasePermission


class MyPermission(BasePermission):
    message = {'msg':'你没有访问该接口的权限！','code':200}

    def has_permission(self, request, view):
        if request.user.role == '0':
            return True
        else:
            return False
