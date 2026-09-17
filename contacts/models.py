from django.conf import settings
from django.db import models


class Contact(models.Model):
    class Tag(models.TextChoices):
        CUSTOMER = "customer", "Kunde"
        PARTNER = "partner", "Partner"
        LEAD = "lead", "Interessent"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    email = models.EmailField()
    tag = models.CharField(max_length=20, choices=Tag.choices)
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name
