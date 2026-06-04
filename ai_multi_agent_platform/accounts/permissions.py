from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):

    def has_permission(self,request,view):

        return (request.user.is_authenticated and request.user.role == 'admin')
    
class IsRecruiterRole(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and request.user.role == 'recruiter')
    
class IsDeveloperRole(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_athenticated and request.user.role == 'developer')