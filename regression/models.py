from django.db import models


# Create your models here.

class Platform_File(models.Model):
    platform = models.CharField(max_length=100)
    platform_file = models.FileField()
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "ID: %s, Platform: %s, Platform_File: %s" % (str(self.id), str(self.platform), str(self.platform_file))


class Activity(models.Model):
    activity = models.CharField(max_length=100)
    list_of_vars = models.TextField(blank=True, null=True)
    platform = models.ForeignKey(Platform_File, on_delete=models.CASCADE)
    AEM = models.FileField()
    NONAEM = models.FileField()

    def __str__(self):
        return "%s - %s - %s" % (str(self.id), str(self.platform.platform), str(self.activity))

class SingleFile(models.Model):
    platform = models.CharField(max_length=100)
    list_of_vars = models.TextField(blank=True, null=True)
    environment = models.CharField(max_length=100)
    single_file = models.FileField()
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s | %s | %s | %s" % (str(self.id), str(self.list_of_vars), str(self.single_file))


