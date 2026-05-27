from django.db import models

# Create your models here.
class ResearchTask(models.Model):
    
    
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('running','Running'),
        ('complete','Complete')
    ]
    
    title = models.CharField(max_length=255)
    query = models.TextField()
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title