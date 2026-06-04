from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES_CHOICES = [
        ('admin','Admin'),
        ('developer','Developer'),
        ('recruiter','Recruiter')
    ]
    
    role = models.CharField(max_length=20,choices=ROLES_CHOICES,default='developer')
    
    bio = models.URLField(blank=True,null=True)
    profile_image = models.URLField(blank=True,null=True)
    
    def __str__(self):
        return self.username