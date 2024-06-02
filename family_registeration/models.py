"""This module contains Django models for representing various entities in the system."""
from django.db import models
from api.models import BaseModel, Auth


class FamilyParentRegisterationDetail(BaseModel):
    """Model family registeration details."""
    ROLE_CHOICES = [
        ('mom', 'Mom'),
        ('dad', 'Dad'),
        ('step-mom', 'Step-Mom'),
        ('step-dad', 'Step-Dad'),
        ('grandma', 'Grandma'),
        ('grandpa', 'Grandpa'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('other', 'Other'),
    ]  

    family_role = models.CharField(max_length=60, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255)
    birth_city = models.CharField(max_length=100)
    current_city = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=100)
    vision = models.TextField(default="")
    mission = models.TextField(default="")
    goals = models.TextField(default="")
    picture = models.ImageField(upload_to='family_hub_pics/', null=True, blank=True)  # Add this line
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True, related_name="fam_parent")

    def __str__(self):
        return f"{self.family_role} - {self.name}"


class FamilyMemberRegisterationDetail(BaseModel):
    """Model family registeration details."""
    ROLE_CHOICES = [
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('niece', 'Niece'),
        ('nephew', 'Nephew'),
        ('grandson', 'Grandson'),
        ('granddaughter', 'Granddaughter'),
        ('other', 'Other'),
    ] 
 
    family_role = models.CharField(max_length=60, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255)
    birth_city = models.CharField(max_length=100)
    current_city = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='family_hub_pics/', null=True, blank=True)  # Add this line
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True, related_name="fam_members")

    def __str__(self):
        return f"{self.family_role} - {self.name}"
 

class FamilyRelationship(BaseModel):
    parent = models.ForeignKey(FamilyParentRegisterationDetail, on_delete=models.CASCADE, blank=True, null=True)
    members = models.ManyToManyField(FamilyMemberRegisterationDetail)

    def __str__(self):
        return f"Parent: {self.parent}, Members: {[str(member) for member in self.members.all()]}"


    