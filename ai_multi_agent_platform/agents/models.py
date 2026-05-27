from django.db import models

# Create your models here.
class Agent(models.Model):
    
    AGENT_TYPE = [
        ('recruiter','Recruiter'),
        ("scheduler",'Sheduler'),
        ("portfolio",'Portfolio')
    ]
    
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50,choices=AGENT_TYPE)
    
    goal = models.TextField()
    is_active = models.BooleanField(default=True)
    created_At= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name