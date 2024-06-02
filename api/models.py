"""This module contains Django models for representing various entities in the system."""
from django.db import models
import uuid
from django.core.files.base import ContentFile
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from xml.etree import ElementTree
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    """Abstract base model with common fields for other models."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    """Model representing roles in the system."""
    value = models.CharField(max_length=20)
    comment = models.TextField()

    def __str__(self):
        return self.value


class Country(BaseModel):
    """Model representing countries."""
    name = models.CharField(max_length=100)


class City(BaseModel):
    """Model representing cities."""
    name = models.CharField(max_length=100)


class Subscription(BaseModel):
    """Model representing subscription plans."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


class Auth(BaseModel):
    """Model representing user authentication information."""
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.TextField()
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    otp = models.PositiveIntegerField(default=0)
    otp_status = models.BooleanField(default=False)
    otp_count = models.PositiveIntegerField(default=0)
    profile = models.ImageField(upload_to='ProfileImage/')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.email


class WhitelistToken(BaseModel):
    """Model representing whitelist tokens for user authentication."""
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    token = models.TextField()


class AdminSubscription(BaseModel):
    """Model representing admin subscriptions."""
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, blank=True, null=True)


class ManagerDetails(BaseModel):
    """Model representing manager details."""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True)
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    admin_subscription = models.ForeignKey(AdminSubscription, on_delete=models.CASCADE, blank=True, null=True)


class FamilyDetails(BaseModel):
    """Model representing family details."""
    family_last_name = models.CharField(max_length=255)
    slogan = models.CharField(max_length=255)
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.family_last_name


class LogoSymbol(BaseModel):
    """Model representing symbols for logos."""
    symbol_name = models.CharField(max_length=50,default="")
    symbol = models.ImageField(upload_to='Logo_Symbol/', null=True, blank=True)

    def __str__(self):
        return self.symbol_name
   

class LogoColor(BaseModel):
    """Model representing colors for logos."""
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    

class LogoSvg(BaseModel):
    """Model representing SVG logos with associated symbols and colors."""
    logo = models.FileField(upload_to='Logo/', null=True, blank=True)
    style = models.ForeignKey(LogoSymbol, on_delete=models.CASCADE, blank=True, null=True)
    svg_code = models.TextField(blank=True, null=True)  # New field to store SVG code


    def save(self, *args, **kwargs):
        # Generate SVG code and save it to the svg_code field
        if self.logo:
            svg_code = self.generate_svg_code()
            self.svg_code = svg_code

        super().save(*args, **kwargs)

    def generate_svg_code(self):
        # Read the content of the SVG file
        with open(self.logo.path, 'r') as svg_file:
            svg_content = svg_file.read()

        # Modify or manipulate the SVG content as needed
        # For demonstration, let's assume we add a title element to the SVG
        root = ElementTree.fromstring(svg_content)
        title_element = ElementTree.Element("title")
        title_element.text = f"Logo: {self.logo.name}"
        root.insert(0, title_element)

        # Convert the modified XML back to SVG code
        modified_svg_code = ElementTree.tostring(root).decode('utf-8')

        return modified_svg_code

@receiver(post_save, sender=LogoSvg)
def update_svg_code(sender, instance, **kwargs):
    if not instance.svg_code and instance.logo:
        svg_code = instance.generate_svg_code()
        instance.svg_code = svg_code
        instance.save()
   

class RelatedSvg(BaseModel):
    """Model representing related SVGs associated with a LogoSvg."""
    logo = models.FileField(upload_to='Related_Logo/', null=True, blank=True)
    style = models.ForeignKey(LogoSymbol, on_delete=models.CASCADE, blank=True, null=True)
    logo_svg = models.ForeignKey(LogoSvg, on_delete=models.CASCADE, blank=True, null=True)
    svg_code = models.TextField(blank=True, null=True)  # New field to store SVG code


    def save(self, *args, **kwargs):
        # Generate SVG code and save it to the svg_code field
        if self.logo:
            svg_code = self.generate_svg_code()
            self.svg_code = svg_code

        super().save(*args, **kwargs)

    def generate_svg_code(self):
        # Read the content of the SVG file
        with open(self.logo.path, 'r') as svg_file:
            svg_content = svg_file.read()

        # Modify or manipulate the SVG content as needed
        # For demonstration, let's assume we add a title element to the SVG
        root = ElementTree.fromstring(svg_content)
        title_element = ElementTree.Element("title")
        title_element.text = f"Logo: {self.logo.name}"
        root.insert(0, title_element)

        # Convert the modified XML back to SVG code
        modified_svg_code = ElementTree.tostring(root).decode('utf-8')

        return modified_svg_code

@receiver(post_save, sender=RelatedSvg)
def update_svg_code(sender, instance, **kwargs):
    if not instance.svg_code and instance.logo:
        svg_code = instance.generate_svg_code()
        instance.svg_code = svg_code
        instance.save()
    

class UserLogo(BaseModel):
    """Model representing user-specific logos."""
    family = models.ForeignKey(FamilyDetails, on_delete=models.CASCADE, blank=True, null=True)
    logo = models.ImageField(upload_to='User_Logo/')
    logo_svg = models.ForeignKey(RelatedSvg, on_delete=models.CASCADE, blank=True, null=True)


# For Initializing PDF for FHB Web Module
class Pdf(BaseModel):
    Font_CHOICES = [
        (0, 'Value 0'),
        (1, 'Value 1'),
        (2, 'Value 2'),
        (3, 'Value 3'),
        (4, 'Value 4'),
        (5, 'Value 5'),
        (6, 'Value 6'),
        (7, 'Value 7'),
    ]
    id = models.IntegerField(primary_key=True)  # You'll set this manually
    user_id = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.CharField(max_length=255,blank=True, null=True)
    name = models.CharField(max_length=255,blank=True, null=True)
    dir = models.CharField(max_length=255,blank=True, null=True)
    family_type = models.CharField(max_length=255,blank=True, null=True)
    is_duplicate = models.CharField(max_length=255,blank=True, null=True)
    font_style = models.IntegerField(choices=Font_CHOICES, blank=True, null=True)

IS_FINISHED_CHOICES = [
    (0, "0"),
    (1, "1")
]

# Module No. 1 CoverPage of the Book (FHB Web Module)
class CoverPage(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    lastname = models.CharField(max_length=255,blank=True, null=True)
    lastname_heading = models.CharField(max_length=255,blank=True, null=True)
    sentence = models.TextField(max_length=255,blank=True, null=True)
    family_type = models.CharField(max_length=255,blank=True, null=True)
    is_duplicate = models.CharField(max_length=255,blank=True, null=True)
    image = models.ImageField(upload_to='images/',blank=True, null=True)
    bg_image = models.ImageField(upload_to='images/',blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)
    sub_title = models.TextField(max_length=255,blank=True, null=True)

    def __str__(self):
        return str(self.pdf_id)


# Module No. 2 Intoduction page of the Book (FHB Web Module)
class IntroductionPage(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    beginning_letter= models.CharField(max_length=100, default="Dear Family", blank=True, null=True)
    tone_used = models.CharField(max_length=100, blank=True, null=True)
    note= models.TextField(blank=True, null=True)
    characters_list = models.TextField(blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)


    def __str__(self):
        return str(self.pdf_id)


# Module No. 3 Family Members of the Book (FHB Web Module) 
class family_bios(BaseModel):
    user_role = (
        ("0", "0"),
        ("1", "1"),
    )
    id = models.IntegerField(primary_key=True)
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    is_begin = models.CharField(choices=user_role, max_length=10, default="0")
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)

 
class parent_members(BaseModel):
    RELATION_CHOICES = [
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
    id = models.IntegerField(primary_key=True)
    family_bios_id = models.ForeignKey(family_bios, on_delete=models.CASCADE, blank=True, null=True)
    relation = models.CharField(max_length=50, choices=RELATION_CHOICES, blank=True, null=True)
    other_relation = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    birth_city = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    dob = models.DateField(auto_now=False, blank=True, null=True)
    profession = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='images/',default="images/dummy.png")
    favourite_food = models.CharField(max_length=255, blank=True, null=True)
    other_favourite_food = models.CharField(max_length=255, blank=True, null=True)
    favourite_holiday = models.CharField(max_length=255, blank=True, null=True)
    other_favourite_holiday = models.CharField(max_length=255, blank=True, null=True)
    afraid_of = models.CharField(max_length=255, blank=True, null=True)
    other_afraid_of = models.CharField(max_length=255, blank=True, null=True)
    other_favourite_quote = models.CharField(max_length=255, blank=True, null=True)
    favourite_quote = models.CharField(max_length=255, blank=True, null=True)
    is_quote = models.IntegerField(default=0)

    def __str__(self):
        return str(self.family_bios_id)

    def clean(self):
        # Ensure only one of relation or other_relation is provided
        if self.relation and self.other_relation:
            raise ValidationError("Only one of 'relation' or 'other_relation' can be provided, not both.")
        
        # Ensure only one of favourite_food or other_favourite_food is provided
        if self.favourite_food and self.other_favourite_food:
            raise ValidationError("Only one of 'favourite_food' or 'other_favourite_food' can be provided, not both.")
        
        # Ensure only one of relation or other_relation is provided
        if self.favourite_holiday and self.other_favourite_holiday:
            raise ValidationError("Only one of 'favourite_holiday' or 'other_favourite_holiday' can be provided, not both.")
        
        # Ensure only one of afraid_of or other_afraid_of is provided
        if self.afraid_of and self.other_afraid_of:
            raise ValidationError("Only one of 'afraid_of' or 'other_afraid_of' can be provided, not both.")
        
        # Ensure only one of favourite_quote or other_favourite_quote is provided
        if self.favourite_quote and self.other_favourite_quote:
            raise ValidationError("Only one of 'favourite_quote' or 'other_favourite_quote' can be provided, not both.")

        if self.family_bios_id:
            # Check for at most 2 parent members in a family
            parent_count = parent_members.objects.filter(family_bios_id=self.family_bios_id).exclude(id=self.id).count()
            if parent_count >= 2:
                raise ValidationError('A family can have at most 2 parent members.')

            # Ensure no duplicate relation in a family
            if self.relation:
                existing_relation = parent_members.objects.filter(family_bios_id=self.family_bios_id, relation=self.relation).exclude(id=self.id)
                if existing_relation.exists():
                    raise ValidationError(f'A family can have at most 1 {self.relation}.')

            # Ensure no duplicate other_relation in a family
            if self.other_relation:
                existing_relation = parent_members.objects.filter(family_bios_id=self.family_bios_id, other_relation=self.other_relation).exclude(id=self.id)
                if existing_relation.exists():
                    raise ValidationError(f'A family can have at most 1 {self.other_relation}.')

    def save(self, *args, **kwargs):
        self.clean()  # Call clean method for validation before saving
        super(parent_members, self).save(*args, **kwargs)



class other_members(BaseModel):
    RELATION_CHOICES = [
    ('son', 'Son'),
    ('daughter', 'Daughter'),
    ('niece', 'Niece'),
    ('nephew', 'Nephew'),
    ('grandson', 'Grandson'),
    ('granddaughter', 'Granddaughter'),
    ('other', 'Other'),
    ]
    id = models.IntegerField(primary_key=True)
    family_bios_id = models.ForeignKey(family_bios, on_delete=models.CASCADE, blank=True, null=True)
    relation = models.CharField(max_length=50, choices=RELATION_CHOICES)
    other_relation = models.CharField(max_length=255,default="")
    full_name = models.CharField(max_length=255,default="")
    birth_city = models.CharField(max_length=255,default="")
    city = models.CharField(max_length=255,default="")
    best_attribute = models.CharField(max_length=255,default="")
    second_best_attribute = models.CharField(max_length=255,default="")
    dob = models.DateField(auto_now=False)
    image = models.ImageField(upload_to='images/',default="")
    email = models.EmailField()
    favourite_food = models.CharField(max_length=255,default="")
    other_favourite_food = models.CharField(max_length=255,default="")
    other_favourite_quote = models.CharField(max_length=255,default="")
    other_best_attribute = models.CharField(max_length=255,default="")
    is_quote = models.IntegerField(default=0)

    def __str__(self):
        return str(self.family_bios_id)

# Module No.4 Core Values of the Book (FHB Web Module)
class CoreValues(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    value_one = models.CharField(max_length=255,blank=True, null=True)
    value_two = models.CharField(max_length=255,blank=True, null=True)
    value_three = models.CharField(max_length=255,blank=True, null=True)
    value_four = models.CharField(max_length=255,blank=True, null=True)
    value_five = models.CharField(max_length=255,blank=True, null=True)
    note= models.TextField(blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)

# Module No.5 VisionStatements of the Book (FHB Web Module)
class VisionStatements(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    heading = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)

# Module No.6 Mission Statements of the Book (FHB Web Module)
class MissionStatements(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    heading = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)


# Module No.7 Code of Conduct of the Book (FHB Web Module)
class CodeOfConducts(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    statement_one = models.CharField(max_length=255, blank=True, null=True)
    statement_two = models.CharField(max_length=255, blank=True, null=True)
    statement_three = models.CharField(max_length=255, blank=True, null=True)
    statement_four = models.CharField(max_length=255, blank=True, null=True)
    statement_five = models.CharField(max_length=255, blank=True, null=True)
    statement_six = models.CharField(max_length=255, blank=True, null=True)
    statement_seven = models.CharField(max_length=255, blank=True, null=True)
    statement_eight = models.CharField(max_length=255, blank=True, null=True)
    statement_nine = models.CharField(max_length=255, blank=True, null=True)
    statement_ten = models.CharField(max_length=255, blank=True, null=True)
    statement_eleven = models.CharField(max_length=255, blank=True, null=True)
    statement_twelve = models.CharField(max_length=255, blank=True, null=True)
    statement_thirteen = models.CharField(max_length=255, blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)


# Module No.8 Family Media Agreement of the Book (FHB Web Module)
class FamilyMediaAgreements(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    statement_one = models.CharField(max_length=255,blank=True, null=True)
    statement_two = models.CharField(max_length=255,blank=True, null=True)
    statement_three = models.CharField(max_length=255,blank=True, null=True)
    statement_four = models.CharField(max_length=255,blank=True, null=True)
    statement_five = models.CharField(max_length=255,blank=True, null=True)
    statement_six = models.CharField(max_length=255,blank=True, null=True)
    statement_seven = models.CharField(max_length=255,blank=True, null=True)
    statement_eight = models.CharField(max_length=255,blank=True, null=True)
    statement_nine = models.CharField(max_length=255,blank=True, null=True)
    statement_ten = models.CharField(max_length=255,blank=True, null=True)
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)


# Module No.9 Family Constitution of the Book (FHB Web Module)
class FamilyConstitutions(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    note = models.TextField(default="")
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)


# Module No.10 Summary of the Book (FHB Web Module)
class Summary(BaseModel):
    pdf_id = models.OneToOneField(Pdf, on_delete=models.CASCADE, blank=True, null=True)
    note = models.TextField(default="")
    is_finished = models.IntegerField(default=0, choices=IS_FINISHED_CHOICES)

    def __str__(self):
        return str(self.pdf_id)

