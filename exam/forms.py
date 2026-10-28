from django import forms

from .models import UserRegistration


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = UserRegistration
        fields = [
            "name",
            "mobile",
            "email",
            "another_name",
            "state",
            "district",
            "gender",
            "date_of_birth",
            "address",
            "photo",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = False  # Adjust if the photo field is optional

    def clean(self):
        cleaned_data = super().clean()
        mobile = cleaned_data.get("mobile")
        email = cleaned_data.get("email")

        if UserRegistration.objects.filter(mobile=mobile).exists():
            self.add_error("mobile", "A user with this mobile number already exists.")

        if UserRegistration.objects.filter(email=email).exists():
            self.add_error("email", "A user with this email address already exists.")

        return cleaned_data
