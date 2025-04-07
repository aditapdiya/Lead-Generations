from django.db import models

class Lead(models.Model):
    name = models.TextField(null=True, blank=True)  # Allows unlimited length
    profile_link = models.URLField()
    source = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Course(models.Model):
    name = models.CharField(max_length=10,unique=True)

    def __str__(self):
        return self.name
    