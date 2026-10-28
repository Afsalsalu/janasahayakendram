import json
import logging
import random

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.core import serializers
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View

logger = logging.getLogger(__name__)
User = get_user_model()
import logging
from decimal import Decimal

import sib_api_v3_sdk
from django.contrib.auth import login as django_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
# CRUD operations
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)
from django_ratelimit.decorators import ratelimit
from sib_api_v3_sdk.rest import ApiException

# forms
from .forms import (AccountMasterForm, CentreUserForm,
                    ComapnyDetailsMasterForm, CustomPasswordChangeForm,
                    CustomPasswordResetForm, DepartmentForm, EmployeeForm,
                    HeadOfficeForm, KeralaSubCentreForm, LoginForm,
                    ServiceFilterForm, StateForm)
# models
from .models import (AboutBlog, AboutPage, AddState, Career, CareerForm,
                     CentreUserAccount, CertificatePayment, Contact,
                     Department, DownloadForm, Employee, FailedLoginAttempt,
                     HeadOffice, HomeLogoBrand,
                     HomeService, KeralaSubCentre, LatestNewsCentre, Media,
                     OnlineClass, Software, State, StateService,
                     Table_Accountsmaster, Table_Acntchild,
                     Table_companyDetailschild, Table_Companydetailsmaster,
                     Table_Contra_Entry, Table_DrCrNote, Table_Journal_Entry,
                     Table_Voucher, VoucherConfiguration, Wallet)


def safe_redirect(request):
    # Use a trusted list of redirect targets
    redirect_target = request.GET.get("next", "/")
    allowed_hosts = ["test.sscegov.com", "sscegov.com"]

    if redirect_target not in allowed_hosts:
        return redirect("/")

    return redirect(redirect_target)

from django.shortcuts import render

def custom_csrf_failure(request, reason=""):
    return render(request, 'web/exam/payment.html', {'reason': reason})

    
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def sensitive_view(request):
    # Your sensitive view logic here
    pass


def logout_view(request):
    logout(request)
    return redirect("/")


def my_view(request):
    response = HttpResponse("Hello, world!")
    response["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://trusted.cdn.com; "
        "style-src 'self' https://trusted.cdn.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    )
    return response


# Helper function to get client's IP address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



@ratelimit(key="ip", rate="5/m", method="ALL", block=True)
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            captcha_response = form.cleaned_data.get("captcha")

            # Authenticate the user
            user = authenticate(request, username=username, password=password)

            if user and captcha_response:  # Check if user is authenticated and CAPTCHA is valid
                if user.is_active:
                    login(request, user)
                    # Clear previous failed login attempts for this user
                    FailedLoginAttempt.objects.filter(user=user).delete()

                    # Redirect based on user type
                    if user.is_superuser:
                        return redirect("web:admin_dashboard")
                    elif user.usertype == "centre":
                        return redirect("web:centre_dashboard")
                    elif user.usertype == "Employee":
                        return redirect("web:employee_dashboard")
                    elif user.usertype == "HeadOffice":
                        return redirect("web:headoffice_dashboard")
                    elif user.usertype == "State":
                        return redirect("web:state_dashboard")
                    elif user.usertype == "Subcentre":
                        return redirect("web:subcentre_dashboard")
                    else:
                        return redirect("web:not_found")
                else:
                    return HttpResponseBadRequest("Your account is inactive.")
            else:
                # Track failed login attempt
                ip_address = get_client_ip(request)  # Get the client's IP address

                if ip_address:  # Ensure we have a valid IP address
                    FailedLoginAttempt.objects.create(user=None, ip_address=ip_address)
                else:
                    messages.error(request, "Could not record login attempt due to missing IP address.")

                return render(
                    request,
                    "web/registration/login.html",
                    {"form": form, "error": "Invalid credentials or CAPTCHA."}, 
                )
        else:
            return render(
                request,
                "web/registration/login.html",
                {"form": form, "error": "Invalid form submission."},
            )
    else:
        form = LoginForm()  
        response = render(request, "web/registration/login.html", {"form": form})
        for cookies in request.COOKIES:
            response.delete_cookie(cookies)
        return response


# class CustomLoginView(LoginView):
#     def form_valid(self, form):
#         user = form.get_user()

#         if not user.is_active:
#             messages.error(
#                 self.request, "Your account is inactive. Please contact support."
#             )
#             return redirect("login")

#         django_login(self.request, user)

#         # Update last_login for CentreUser
#         if hasattr(user, "centre"):
#             user.centre.last_login = timezone.now()
#             user.centre.save()

#         if user.is_superuser:
#             return redirect("web:admin_dashboard")
#         elif user.usertype == "centre":
#             return redirect("web:centre_dashboard")
#         elif user.usertype == "Employee":
#             return redirect("web:employee_dashboard")
#         elif user.usertype == "HeadOffice":
#             return redirect("web:headoffice_dashboard")
#         elif user.usertype == "State":
#             return redirect("web:state_dashboard")
#         elif user.usertype == "Subcentre":
#             return redirect("web:subcentre_dashboard")
#         else:
#             return redirect("web:not_found")


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "web/change_password.html"
    success_url = reverse_lazy("web/custom_login")

    def get_success_url(self):
        return reverse_lazy("web:custom_login")


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    email_template_name = "web/registration/password_reset_email.html"
    subject_template_name = "web/registration/password_reset_subject.txt"
    template_name = "web/registration/password_reset_form.html"
    success_url = reverse_lazy("web:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        associated_users = User.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                context = {
                    "email": user.email,
                    "domain": self.request.META["HTTP_HOST"],
                    "site_name": "Your site name",
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    "token": default_token_generator.make_token(user),
                    "protocol": "https" if self.request.is_secure() else "http",
                }
                subject = render_to_string(self.subject_template_name, context)
                subject = "".join(subject.splitlines())
                email_message = render_to_string(self.email_template_name, context)
                try:
                    send_mail(
                        subject, email_message, "your_email@example.com", [user.email]
                    )
                    logger.info(f"Password reset email sent to {user.email}")
                except Exception as e:
                    logger.error(f"Error sending password reset email: {e}")
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "web/registration/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "web/registration/password_reset_confirm.html"
    success_url = reverse_lazy("web:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "web/registration/password_reset_complete.html"


# Home Page
def notfound(request, exception=None):
    return render(request, "web/404.html", status=404)


def index(request):
    home_services = HomeService.objects.all()
    blogs = AboutBlog.objects.all()
    logos = HomeLogoBrand.objects.all()
    context = {
        "blogs": blogs,
        "home_services": home_services,
        "logos": logos,
    }
    return render(request, "web/home/index.html", context)


def whatwedo(request):
    return render(request, "web/home/whatwedo.html")


def contact(request):
    if request.method == "POST":
        # Get form data
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        centre_name = request.POST.get("centre_name")
        state = request.POST.get("state")
        district = request.POST.get("district")
        taluk = request.POST.get("taluk")
        subject = request.POST.get("subject")
        comments = request.POST.get("comments")

        # reCAPTCHA validation
        recaptcha_response = request.POST.get("g-recaptcha-response")
        data = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response,
        }
        r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = r.json()

        if result["success"]:
            # Save contact form data to the database
            contact = Contact(
                full_name=full_name,
                phone=phone,
                email=email,
                centre_name=centre_name,
                state=state,
                district=district,
                taluk=taluk,
                subject=subject,
                comments=comments,
            )
            contact.save()
            return redirect("web:contact")
        else:
            # reCAPTCHA validation failed, return an error message
            context = {
                "error_message": "Invalid reCAPTCHA. Please try again.",
                "full_name": full_name,
                "phone": phone,
                "email": email,
                "centre_name": centre_name,
                "state": state,
                "district": district,
                "taluk": taluk,
                "subject": subject,
                "comments": comments,
            }
            return render(request, "web/home/contact.html", context)

    # Handle GET request or when form submission is not successful
    return render(request, "web/home/contact.html")


class MediaListView(ListView):
    model = Media
    template_name = "web/home/media.html"
    context_object_name = "media"


def about(request):
    about_content = AboutPage.objects.first()  # Query the AboutPage content
    blogs = AboutBlog.objects.all()  # Query all the blogs
    about_logos = HomeLogoBrand.objects.all()  # Query all the About Logos

    context = {
        "about_content": about_content,
        "blogs": blogs,
        "about_logos": about_logos,
    }
    return render(request, "web/home/about.html", context)


class Admin(ListView):
    model = Career
    template_name = "web/home/career.html"
    context_object_name = "career"


class CareerListView(ListView):
    model = Career
    template_name = "web/home/career.html"
    context_object_name = "career"


def privacy_policy(request):
    return render(request, "web/home/privacy_policy.html")


def terms_and_conditions(request):
    return render(request, "web/home/terms_and_conditions.html")


def exam(request):
    return render(request, "web/home/exam.html")


def maintenance(request):
    return render(request, "web/maintenance.html")


def main(request):
    return render(request, "web/home/main.html")


def offline(request):
    return render(request, "web/offline.html")


def career_role(request):
    return render(request, "web/career_role.html")


def centre_contact(request):
    return render(request, "web/centre/centre_contact.html")


# ----------------------------------------------------------------------------------------------- #
# -------------------------------| ADMIN & HEADOFFICE DASHBOARD START |-------------------------- #
# ----------------------------------------------------------------------------------------------- #


class AdminOrHeadOfficeRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.usertype not in ["Administrator", "HeadOffice"]:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("web:not_found")
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/admin_panel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_kerala = CentreUserAccount.objects.count()
        departments = Department.objects.all()
        headoffice = HeadOffice.objects.count()
        total_employees = Employee.objects.count()
        total_state = State.objects.count()
        total_service = StateService.objects.count()

        context.update(
            {
                "total_kerala": total_kerala,
                "departments": departments,
                "headoffice": headoffice,
                "total_employees": total_employees,
                "total_state": total_state,
                "total_service": total_service,
            }
        )

        user_details = []

        # Limiting the contacts to only 6
        contacts = Contact.objects.all()[:6]
        context["contacts"] = contacts

        request = self.request
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        context["ip"] = ip

        return context


# Admin - Headoffice


class AddHeadOfficeView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = HeadOffice
    form_class = HeadOfficeForm
    template_name = "web/admin_panel/headoffice/add_headoffice.html"
    success_url = reverse_lazy("web:headoffice_list")

    def form_valid(self, form):
        # Generate username as HO followed by 8 random numbers
        username = f"HO{random.randint(10000000, 99999999)}"

        # Set the password as the phone number
        password = form.cleaned_data["phone_number"]

        # Create the user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=form.cleaned_data["email"],
            usertype="HeadOffice",
        )

        # Assign the newly created user to the HeadOffice object
        form.instance.user = user

        # Save the HeadOffice object
        self.object = form.save()

        # Prepare the email content
        subject = "Welcome to the Janasahayakendram"
        html_content = (
            f"<p>Thank you for registering. Your account has been created successfully.</p>"
            # f"<p><strong>Centre ID:</strong> {self.object.id}</p>"
            f"<p><strong>Centre Username:</strong> {username}</p>"
            f"<p><strong>Password:</strong> {password}</p>"
            f"<p>We recommend you change your password after logging in.</p>"
            f"<p>For more information, visit our website: <a href='https://janasahayakendram.in/'>https://janasahayakendram.in/</a></p>"
            f"<p>Best regards,<br>The Janasahayakendram Team</p>"
        )

        # Send email using Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        email_data = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": form.cleaned_data["email"]}],
            subject=subject,
            html_content=html_content,
            sender={
                "name": "Janasahayakendram",
                "email": "samatwaservicecenter.gov.in@gmail.com",
            },
        )

        try:
            api_response = api_instance.send_transac_email(email_data)
            print("Email sent successfully:", api_response)
        except ApiException as e:
            print("Exception when sending email: %s\n" % e)

        return super().form_valid(form)


class HeadofficeListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = HeadOffice
    template_name = "web/admin_panel/headoffice/headoffice_list.html"
    context_object_name = "headoffices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_headoffice = HeadOffice.objects.count()
        context.update(
            {
                "total_headoffice": total_headoffice,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Handle file upload
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            with open("uploaded_file.txt", "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, "File uploaded successfully!")
        else:
            messages.error(request, "No file uploaded!")

        return response


class EditHeadOfficeView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = HeadOffice
    form_class = HeadOfficeForm
    template_name = "web/admin_panel/headoffice/add_headoffice.html"
    success_url = reverse_lazy("web:headoffice_list")


class DeleteHeadOfficeView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = HeadOffice
    success_url = reverse_lazy("web:headoffice_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class HeadofficeDashboardView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/headoffice/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_kerala = CentreUserAccount.objects.count()
        departments = Department.objects.all()
        total_employees = Employee.objects.count()
        total_state = State.objects.count()
        total_service = StateService.objects.count()

        context.update(
            {
                "total_kerala": total_kerala,
                "departments": departments,
                "total_employees": total_employees,
                "total_state": total_state,
                "total_service": total_service,
            }
        )

        request = self.request
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        context["ip"] = ip  # Add IP address to the context

        return context


# Admin - State dashboard
class AddStateAdminView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = State
    form_class = StateForm
    template_name = "web/admin_panel/state/add_state_admin.html"
    success_url = reverse_lazy("web:admin_state_list")

    def form_valid(self, form):
        try:
            # Save the state object without committing to the database
            state = form.save(commit=False)
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            email = form.cleaned_data.get("email")

            # Check for missing data
            if not username or not password or not email:
                messages.error(
                    self.request, "Username, password, and email are required."
                )
                return self.form_invalid(form)

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                usertype="state",
                is_active=True,
            )

            # Link the new user to the state object
            state.user = user
            state.save()  # Save the state object with the user linked

            # Optionally, authenticate and log in the user
            user = authenticate(username=username, password=password)
            if user is not None:
                login(self.request, user)

            # Success message using SweetAlert
            messages.success(
                self.request,
                "State user added successfully.",
            )

            return super().form_valid(form)

        except IntegrityError:
            # Handle the case where the username already exists
            messages.error(self.request, "Username already exists.")
            return self.form_invalid(form)

        except Exception as e:
            # General exception handling
            messages.error(self.request, f"An error occurred: {str(e)}")
            return self.form_invalid(form)


class AdminStateListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = State
    template_name = "web/admin_panel/state/state_list.html"
    context_object_name = "states"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Handle file upload
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            with open("uploaded_file.txt", "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, "File uploaded successfully!")
        else:
            messages.error(request, "No file uploaded!")

        return response


class EditStateView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = State
    form_class = StateForm
    template_name = "web/admin_panel/state/add_state_admin.html"
    success_url = reverse_lazy("web:admin_state_list")


class DeleteStateView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = State
    success_url = reverse_lazy("web:admin_state_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


# Admin - centre


def generate_unique_username():
    while True:
        username = "".join([str(random.randint(0, 9)) for _ in range(12)])
        if not User.objects.filter(username=username).exists():
            return username


# A decorator to check if the user is either an Administrator or HeadOffice
def admin_or_headoffice_required(user):
    return user.usertype in ["Administrator", "HeadOffice"]


@method_decorator(user_passes_test(admin_or_headoffice_required), name="dispatch")
class AddCentreUserAdminView(CreateView):
    model = CentreUserAccount
    form_class = CentreUserForm
    template_name = "web/admin_panel/franchise/add_centre_admin.html"
    success_url = reverse_lazy("web:franchise_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        self.object = form.save(
            commit=False
        )  # Create the form object but don't save yet

        # Generate unique username and set user credentials
        username = generate_unique_username()
        password = str(form.cleaned_data["mobile"])
        email = form.cleaned_data["email"]

        # Create the related user
        user = User.objects.create_user(
            username=username, password=password, email=email
        )
        user.usertype = "centre"
        user.is_active = form.cleaned_data.get("is_active", True)
        user.save()

        # Assign the user to the CentreUserAccount instance
        self.object.user = user
        self.object.is_active = form.cleaned_data.get("is_active", True)
        self.object.created_by = self.request.user  # Set the creator
        self.object.save()  # Now save the form object with the related user

        # Prepare and log email content
        subject = "Welcome to the Janasahayakendram"
        html_content = (
            f"<p>Thank you for registering. Your account has been created successfully.</p>"
            # f"<p><strong>Centre ID:</strong> {self.object.formatted_id}</p>"
            f"<p><strong>Username:</strong> {username}</p>"
            f"<p><strong>Password:</strong> {password}</p>"
            f"<p>We recommend you change your password after logging in.</p>"
            f"<p>For more information, visit our website: <a href='https://janasahayakendram.in/'>https://janasahayakendram.in/</a></p>"
            f"<p>Best regards,<br>The Janasahayakendram Team</p>"
        )

        print("Email content:", html_content)

        # Send the email via Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        email_data = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            subject=subject,
            html_content=html_content,
            sender={
                "name": "Janasahayakendram",
                "email": "samatwaservicecenter.gov.in@gmail.com",
            },
        )

        try:
            api_response = api_instance.send_transac_email(email_data)
            print("Email sent successfully:", api_response)
        except ApiException as e:
            print("Exception when sending email: %s\n" % e)

        return super().form_valid(form)


class EditCentreUserView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = CentreUserAccount
    form_class = CentreUserForm
    template_name = "web/admin_panel/franchise/add_centre_admin.html"
    success_url = reverse_lazy("web:franchise_list")

    def form_valid(self, form):
        user = self.object.user
        user.email = form.cleaned_data["email"]

        password = form.cleaned_data.get("password")
        if password:
            user.set_password(password)  # Only update the password if provided

        user.is_active = form.cleaned_data.get(
            "is_active", True
        )  # Update activation status
        user.save()
        form.instance.user = user
        form.instance.is_active = user.is_active  # Ensure form reflects user status
        return super().form_valid(form)


class AdminCentreUserListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = CentreUserAccount
    template_name = "web/admin_panel/franchise/franchise_list.html"
    context_object_name = "centreusers"

    def get_queryset(self):
        return CentreUserAccount.objects.all()


class AdminCenterUserDetailView(AdminOrHeadOfficeRequiredMixin, DetailView):
    model = CentreUserAccount
    template_name = "web/admin_panel/franchise/centre_profile.html"
    context_object_name = "centreusers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        created_by = self.object.created_by
        context["created_by_username"] = (
            created_by.username if created_by else "Unknown"
        )
        return context


class AdminCentreUserDeleteView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = CentreUserAccount
    success_url = reverse_lazy("web:franchise_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class CentreWalletTransListView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/admin_panel/franchise/wallet_transactions.html"


class CentreNonActiveListView(LoginRequiredMixin, ListView):
    model = CentreUserAccount
    template_name = "web/admin_panel/franchise/non_active_centre.html"
    context_object_name = "non_active_centres"

    def get_queryset(self):
        # Filter to get only inactive users
        return CentreUserAccount.objects.filter(user__is_active=False)


class AddSoftwareView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = Software
    fields = ["title", "logo", "site_link"]
    template_name = "web/admin_panel/franchise/add_software.html"
    success_url = reverse_lazy("web:software_list")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class CentreSoftwareListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = Software
    template_name = "web/admin_panel/franchise/software_list.html"
    context_object_name = "softwares"


class EditSoftwareView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = Software
    fields = ["title", "logo", "site_link"]
    template_name = "web/admin_panel/franchise/add_software.html"
    success_url = reverse_lazy("web:software_list")


# Admin - Employee Department
class DepartmentListView(AdminOrHeadOfficeRequiredMixin, View):
    model = Department
    template_name = "web/admin_panel/employee/department.html"

    def get(self, request):
        form = DepartmentForm()
        departments = self.model.objects.all()
        return render(
            request, self.template_name, {"departments": departments, "form": form}
        )

    def post(self, request):
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("web:department_list")
        departments = self.model.objects.all()
        return render(
            request, self.template_name, {"departments": departments, "form": form}
        )


# Admin - Employee
class AddEmployeeView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "web/admin_panel/employee/add_employee.html"
    success_url = reverse_lazy("web:employee_list")

    def form_valid(self, form):
        employee = form.save(commit=False)
        password = form.cleaned_data.get("password")
        user = User.objects.create_user(
            username=employee.email,
            email=employee.email,
            password=password,
            is_staff=True,
            usertype="Employee",
        )
        employee.user = user
        employee.save()
        messages.success(
            self.request, f"Employee '{employee.name}' added successfully."
        )
        return super().form_valid(form)


class AddOnlineClassView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = OnlineClass
    template_name = "web/admin_panel/franchise_dashboard/add_online_class.html"
    fields = ["title", "class_video_link", "description", "thumbnail"]
    success_url = reverse_lazy("web:onlineclass_list")


class OnlineClassListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = OnlineClass
    template_name = "web/admin_panel/franchise_dashboard/onlineclass_list.html"
    context_object_name = "onlineclass"


class EmployeeDetailView(AdminOrHeadOfficeRequiredMixin, DetailView):
    model = Employee
    template_name = "web/admin_panel/employee/admin_employee_profile.html"
    context_object_name = "employees"


class EmployeeListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = Employee
    template_name = "web/admin_panel/employee/employee_list.html"
    context_object_name = "employees"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_employees"] = self.model.objects.count()
        return context


class EditEmployeeView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "web/admin_panel/employee/add_employee.html"
    success_url = reverse_lazy("web:employee_list")


class DeleteEmployeeView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("web:employee_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


# Admin - Online Class
class EditOnlineClassView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = OnlineClass
    fields = ["title", "class_video_link", "thumbnail", "description"]
    template_name = "web/admin_panel/franchise_dashboard/add_online_class.html"
    success_url = reverse_lazy("web:onlineclass_list")


class DeleteOnlineClassView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = OnlineClass
    success_url = reverse_lazy("web:onlineclass_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


# admin contact details
class ContactListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = Contact
    template_name = "web/admin_panel/home/contact_list.html"
    context_object_name = "contacts"


class DeleteContactView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = Contact
    success_url = reverse_lazy("web:contact_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


# Admin  media
class MediaAdminListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = Media
    template_name = "web/admin_panel/home/media_list.html"
    context_object_name = "media"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titles"] = Media.objects.values_list("title", flat=True).distinct()
        selected_title = self.request.GET.get("title", "")
        if selected_title:
            context["media"] = Media.objects.filter(title=selected_title)
        else:
            context["media"] = Media.objects.all()
        return context


class MediaAdminCreateView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = Media
    template_name = "web/admin_panel/home/add_media.html"
    fields = ["image", "sub_title", "title", "content", "place"]
    success_url = reverse_lazy("web:media_list")


class EditMediaView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = Media
    fields = ["image", "sub_title", "title", "content", "place"]
    template_name = "web/admin_panel/home/add_media.html"
    success_url = reverse_lazy("web:media_list")


class DeleteMediaView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = Media
    success_url = reverse_lazy("web:media_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


# Exam Registration
# class ExamRegisterListView(AdminOrHeadOfficeRequiredMixin, ListView):
#     model = UserRegistration
#     template_name = "web/admin_panel/franchise_dashboard/exam_register_list.html"
#     context_object_name = "examregister"

#     def post(self, request, *args, **kwargs):
#         response = super().post(request, *args, **kwargs)
#         # Handle file upload
#         uploaded_file = request.FILES.get("file")
#         if uploaded_file:
#             with open("uploaded_file.txt", "wb+") as destination:
#                 for chunk in uploaded_file.chunks():
#                     destination.write(chunk)
#             messages.success(request, "File uploaded successfully!")
#         else:
#             messages.error(request, "No file uploaded!")

#         return response


class ErrorView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/admin_panel/error.html"


class FaqView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/centre/faq.html"


class AddDownloadFormView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = DownloadForm
    fields = ["title", "pdf"]
    template_name = "web/admin_panel/franchise_dashboard/add_downloadform.html"
    success_url = reverse_lazy("web:downloadform_list")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class DownloadFormAdminListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = DownloadForm
    template_name = "web/admin_panel/franchise_dashboard/downloadform_list.html"
    context_object_name = "download_forms"


class EditDownloadFormView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = DownloadForm
    fields = ["title", "pdf"]
    template_name = "web/admin_panel/franchise_dashboard/add_downloadform.html"
    success_url = reverse_lazy("web:downloadform_list")


class DeleteDownloadFormView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = DownloadForm
    success_url = reverse_lazy("web:downloadform_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class CareerAddAdminView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = Career
    template_name = "web/admin_panel/home/add_career.html"
    fields = ["name_of_host", "experience", "qualification", "salary"]
    success_url = reverse_lazy("web:career_list")


class CareerAdminListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = Career
    template_name = "web/admin_panel/home/career_list.html"
    context_object_name = "career"


class DeleteCareerView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = Career
    success_url = reverse_lazy("web:career_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class CareerCreateView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = CareerForm
    fields = [
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "job_title",
        "experience_years",
        "qualification",
        "age",
        "current_role",
        "resume",
        "experience_level",
        "work_preference",
        "comments",
    ]
    template_name = "web/home/career_form.html"
    success_url = reverse_lazy("web:career_form")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"message": "Career form submitted successfully!"})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["careers"] = Career.objects.all()
        return context


class CareerApplicationsList(AdminOrHeadOfficeRequiredMixin, ListView):
    model = CareerForm
    template_name = "web/admin_panel/home/career_applications.html"
    context_object_name = "applications"


class DeleteCareerApplicationsView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = CareerForm
    success_url = reverse_lazy("web:career_applications")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object.delete()
            return JsonResponse({"success": True})
        else:
            self.object.delete()
            return redirect(self.success_url)


class AdminKeralaSubCentreView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/admin_panel/franchise/admin_kerala_subcentre.html"


class AddStateCreateView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = AddState
    fields = ["state_name", "logo"]
    template_name = "web/admin_panel/services/addstate_form.html"
    success_url = reverse_lazy("web:all_sections")


class AddStateListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = AddState
    template_name = "web/admin_panel/services/addstate_list.html"
    context_object_name = "states"


class AddStateUpdateView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = AddState
    fields = ["state_name", "logo"]
    template_name = "web/admin_panel/services/addstate_form.html"
    success_url = reverse_lazy("web:addstate_list")


class AddStateDeleteView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = AddState
    success_url = reverse_lazy("web:addstate_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class StateServiceListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = StateService
    template_name = "web/admin_panel/services/stateservice_list.html"
    context_object_name = "services"


class StateServiceCreateView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = StateService
    fields = ["service_name", "service_logo", "service_link", "is_active", "is_popular"]
    template_name = "web/admin_panel/services/stateservice_form.html"

    def form_valid(self, form):
        state_slug = self.kwargs["state_slug"]
        state = AddState.objects.get(slug=state_slug)
        form.instance.state = state
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "web:stateservice_by_state",
            kwargs={"state_slug": self.kwargs["state_slug"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state"] = AddState.objects.get(slug=self.kwargs["state_slug"])
        return context


class StateServiceUpdateView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = StateService
    fields = ["service_name", "service_logo", "service_link", "is_active", "is_popular"]
    template_name = "web/admin_panel/services/stateservice_form.html"

    def form_valid(self, form):
        # Proceed to save if the form is valid
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Print form errors for debugging
        return super().form_invalid(form)

    def get_success_url(self):
        state_slug = self.object.state.slug
        return reverse_lazy(
            "web:stateservice_by_state", kwargs={"state_slug": state_slug}
        )


from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.shortcuts import redirect
from .models import StateService

class StateServiceDeleteView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = StateService

    def get_success_url(self):
        # Assuming your StateService model has a ForeignKey to AddState model named 'state'
        state_slug = self.object.state.slug
        return reverse_lazy("web:stateservice_by_state", kwargs={"state_slug": state_slug})

    def post(self, request, *args, **kwargs):
        # Get the object to delete
        self.object = self.get_object()
        self.object.delete()

        # Redirect to the success URL after deletion
        return redirect(self.get_success_url())



class AllSectionView(AdminOrHeadOfficeRequiredMixin, TemplateView):
    template_name = "web/admin_panel/services/all_section.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["states"] = AddState.objects.all()
        return context


class StateServiceByStateView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = StateService
    template_name = "web/admin_panel/services/state_services_by_state.html"
    context_object_name = "services"

    def get_queryset(self):
        state_slug = self.kwargs["state_slug"]
        return StateService.objects.filter(state__slug=state_slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["state"] = AddState.objects.get(slug=self.kwargs["state_slug"])
        return context


class LatestNewsCentreAddView(AdminOrHeadOfficeRequiredMixin, CreateView):
    model = LatestNewsCentre
    template_name = "web/admin_panel/franchise/add_news_centre.html"
    fields = ["image", "title", "content"]
    success_url = reverse_lazy("web:latest_news_list")


class LatestNewsCentreListView(AdminOrHeadOfficeRequiredMixin, ListView):
    model = LatestNewsCentre
    template_name = "web/admin_panel/franchise/news_centre_list.html"
    context_object_name = "latest_news"


class EditLatestNewsCentreView(AdminOrHeadOfficeRequiredMixin, UpdateView):
    model = LatestNewsCentre
    fields = ["image", "title", "content"]  # Use fields instead of form_class list
    template_name = "web/admin_panel/franchise/add_news_centre.html"
    success_url = reverse_lazy("web:latest_news_list")


class DeleteLatestNewsCentreView(AdminOrHeadOfficeRequiredMixin, DeleteView):
    model = LatestNewsCentre
    success_url = reverse_lazy("web:latest_news_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


@login_required
def service_list(request):
    form = ServiceFilterForm(request.GET or None)
    services = StateService.objects.all()

    if form.is_valid():
        show_popular = form.cleaned_data.get("show_popular")
        if show_popular:
            services = services.filter(is_popular=True)

    return render(
        request,
        "web/admin_panel/services/popular_service.html",
        {"form": form, "services": services},
    )


# ----------------------------------------X---------------------X-------------------------------- #
# ---------------------------------| ADMIN & HEADOFFICE DASHBOARD END |-------------------------- #
# ----------------------------------------X---------------------X---------------------------------#


# ----------------------------------------------------------------------------------------------- #
# ------------------------------------| KERALA CENTRE DASHBOARD START |-------------------------- #
# ----------------------------------------------------------------------------------------------- #


class KeralaRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.usertype != "centre":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("web:not_found")
        return super().dispatch(request, *args, **kwargs)


class DistrictDashboardView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/centre_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            # Try to get the related centre
            district_detail = user.centre  # Assuming user has a related 'centre'
        except ObjectDoesNotExist:
            raise Http404("User has no associated centre.")

        latest_news = LatestNewsCentre.objects.all()
        popular_services = StateService.objects.filter(is_popular=True, is_active=True)

        context.update(
            {
                "latest_news": latest_news,
                "district_detail": district_detail,
                "popular_services": popular_services,
                "last_login": user.centre.last_login if user.centre else None,
            }
        )

        request = self.request
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        context["ip"] = ip

        return context


class CenterWalletHistoryView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/wallet/history.html"


class CenterAddWalletView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/wallet/add_wallet.html"


class DownloadFormListView(KeralaRequiredMixin, ListView):
    model = DownloadForm
    template_name = "web/franchise/download_form_list.html"
    context_object_name = "download_forms"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        uploaded_file = request.FILES.get("pdf")
        if uploaded_file:
            DownloadForm.objects.create(title="Uploaded File", pdf=uploaded_file)
            messages.success(request, "File uploaded successfully!")
        else:
            messages.error(request, "No file uploaded!")

        return response


class DownloadFileView(View):
    def get(self, request, *args, **kwargs):
        try:
            download_form = DownloadForm.objects.get(pk=kwargs["pk"])
            file_path = download_form.pdf.path
            return FileResponse(open(file_path, "rb"), as_attachment=True)
        except DownloadForm.DoesNotExist:
            pass


class SoftwareView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/tool.html"


class OnlineClassView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/online_class.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve necessary data
        onlineclass = OnlineClass.objects.all()

        context = {
            "onlineclass": onlineclass,
        }
        return context


class SoftwaresView(KeralaRequiredMixin, ListView):
    model = Software
    template_name = "web/franchise/softwares.html"
    context_object_name = "softwares"


class AddKeralaSubCentreView(KeralaRequiredMixin, CreateView):
    model = KeralaSubCentre
    form_class = KeralaSubCentreForm
    template_name = "web/franchise/add_subcentre.html"
    success_url = reverse_lazy("web:kerala_subcentre")

    def form_valid(self, form):
        try:
            state = form.save(commit=False)
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            name = form.cleaned_data.get("name")
            user = User.objects.create_user(
                username=username,
                email=username,
                password=password,
                usertype="subcentre",
                is_active=True,
            )
            state.user = user
            state.name = name
            state.save()
            messages.success(
                self.request,
                f"State added successfully. Username: {username}, Password: {password}",
            )
            user = authenticate(username=username, password=password)
            if user is not None:
                login(self.request, user)
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, "Username already exists.")
            return HttpResponseRedirect(reverse_lazy("web:error"))


class KeralaSubCentreView(LoginRequiredMixin, TemplateView):
    model = KeralaSubCentre
    template_name = "web/franchise/sub_centre.html"
    context_object_name = "keralasubcentre"

    def post(self, request, *args, **kwargs):

        response = super().post(request, *args, **kwargs)

        # Handle file upload
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            with open("uploaded_file.txt", "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, "File uploaded successfully!")
        else:
            messages.error(request, "No file uploaded!")

        return response


class CenterWalletView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/wallet/wallet.html"


class StateListView(ListView):
    model = AddState
    template_name = "web/franchise/services/state_list.html"
    context_object_name = "states"


class StateDetailView(DetailView):
    model = AddState
    template_name = "web/franchise/services/state_detail.html"
    context_object_name = "state"
    slug_field = "slug"
    slug_url_kwarg = "slug"


import pdfkit
from django.conf import settings
from django.http import HttpResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

from .constants import PaymentStatus


class DistrictProfileView(KeralaRequiredMixin, TemplateView):
    template_name = "web/franchise/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            centreusers = CentreUserAccount.objects.get(user=user)
            context["centreusers"] = centreusers
        except CentreUserAccount.DoesNotExist:
            context["centreusers"] = None

        # Add Razorpay Key ID to context
        context["razorpay_key_id"] = settings.RAZORPAY_KEY_ID
        return context


@login_required
@csrf_exempt
def centre_certificate_payment(request):
    # Process only POST requests
    if request.method == "POST":
        # Parse JSON data from the request body
        data = json.loads(request.body)
        payment_id = data.get("razorpay_payment_id")
        provider_order_id = data.get("provider_order_id")
        signature_id = data.get("signature_id")

        # Optional: Verify payment with Razorpay or other verification services
        # (Implementation depends on specific verification needs)

        # Retrieve the user registration profile
        profile = CentreUserAccount.objects.get(user=request.user)
        # Mark the certificate as paid
        profile.certificate_paid = True
        profile.save()

        # Record the payment details in the Payment model
        CertificatePayment.objects.create(
            user_registration=profile,
            amount=2.0,  # Amount in INR
            status=PaymentStatus.COMPLETED,
            provider_order_id=provider_order_id,
            payment_id=payment_id,
            signature_id=signature_id,
            is_certificate_payment=True,
        )

        # Return a JSON response indicating success
        return JsonResponse({"success": True})

    # Return a JSON response indicating failure for non-POST requests
    return JsonResponse({"success": False})


class CentreCertificateView(View):
    def get(self, request, *args, **kwargs):
        user_registration = get_object_or_404(CentreUserAccount, user=request.user)

        # Use Django's static file handling to get the image URL
        image_url = request.build_absolute_uri(static("web/images/ssc-certificate.jpg"))

        # Render the HTML template with context data
        html_string = render_to_string(
            "web/franchise/certificate.html",
            {
                "content": user_registration.owner_centre,
                "district": user_registration.district,
                "state": user_registration.state,
                "formatted_id": user_registration.formatted_id,
                "photo": request.build_absolute_uri(
                    user_registration.photo.url
                ),  # Ensure the photo URL is absolute
                "image_url": image_url,
            },
        )

        # Specify the full path to wkhtmltopdf
        path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # Define options for pdfkit
        options = {
            "page-width": "900px",
            "page-height": "650px",
            "margin-top": "0px",
            "margin-right": "0px",
            "margin-bottom": "0px",
            "margin-left": "0px",
            "no-outline": None,
            "enable-local-file-access": None,
            "no-stop-slow-scripts": None,
        }

        # Generate PDF from the HTML string with custom options
        pdf = pdfkit.from_string(
            html_string, False, configuration=config, options=options
        )

        # Determine if the user wants to view or download the PDF
        response = HttpResponse(pdf, content_type="application/pdf")
        if "download" in request.GET:
            response["Content-Disposition"] = (
                f'attachment; filename="certificate_{user_registration.id}.pdf"'
            )
            user_registration.certificate_downloaded = True
            user_registration.save()
        else:
            response["Content-Disposition"] = "inline"

        return response


# --------------------------------------X-----------------------------X-------------------------- #
# --------------------------------------| KERALA CENTRE DASHBOARD END |-------------------------- #
# --------------------------------------X-----------------------------X-------------------------- #

# ----------------------------------------------------------------------------------------------- #
# ---------------------------------------| STATE DASHBOARD START |------------------------------- #
# ----------------------------------------------------------------------------------------------- #


class StateRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.usertype != "State":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("web:not_found")
        return super().dispatch(request, *args, **kwargs)


class StateDashboardView(StateRequiredMixin, TemplateView):
    template_name = "web/state/state_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            state = State.objects.get(user=user)
            if state.state.lower() == "kerala":
                kerala_centres = CentreUserAccount.objects.filter(state=state.state)
                context["kerala_centres"] = kerala_centres
                context["user_state"] = state
            else:
                context["kerala_centres"] = None
        except State.DoesNotExist:
            context["kerala_centres"] = None
        return context


class KeralaStateEdistrictServiceView(StateRequiredMixin, TemplateView):
    template_name = "web/state/edistrict.html"


class KeralaStateWalletView(StateRequiredMixin, TemplateView):
    template_name = "web/state/state_wallet.html"


class AllKeralaService(StateRequiredMixin, TemplateView):
    template_name = "web/state/all_service.html"


# ----------------------------------------X---------------------X-------------------------------- #
# ----------------------------------------| STATE DASHBOARD END |-------------------------------- #
# ----------------------------------------X---------------------X---------------------------------#


# ----------------------------------------------------------------------------------------------- #
# ---------------------------------------| ACCOUNTING START |------------------------------------ #
# ----------------------------------------------------------------------------------------------- #



# ####################################- ACCOUNTS -####################################################

# - Voucher
class VoucherConfigurationListView(LoginRequiredMixin, ListView, View):
    model = VoucherConfiguration
    template_name = 'web/accounts/voucher-configuration/voucher_configuration.html'
    success_url = reverse_lazy('web:voucher_configuration')

    def get(self, request, *args, **kwargs):
        configurations = VoucherConfiguration.objects.all()
        next_serial_numbers = {}

        for config in configurations:
            category_series = (config.category, config.series)
            last_serial = VoucherConfiguration.objects.filter(
                category=config.category,
                series=config.series
            ).order_by('-serial_no').first()
            if last_serial:
                next_serial_numbers[category_series] = last_serial.serial_no + 1
            else:
                next_serial_numbers[category_series] = 1

        context = {
            'object_list': configurations,
            'next_serial_numbers': next_serial_numbers
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        category = request.POST.get('category')
        series = request.POST.get('series')
        serial_no = request.POST.get('serial_no')

        if category and series and serial_no:
            try:
                VoucherConfiguration.objects.create(
                    category=category,
                    series=series,
                    serial_no=serial_no
                )
                return JsonResponse({'success': True, 'redirect_url': self.success_url})
            except IntegrityError:
                context = {
                    'object_list': VoucherConfiguration.objects.all(),
                    'error': 'This combination of category and series already exists.'
                }
                return render(request, self.template_name, context)
        else:
            context = {
                'object_list': VoucherConfiguration.objects.all(),
                'error': 'All fields are required.'
            }
            return render(request, self.template_name, context)


class ValidateVoucherConfiguration(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        series = request.GET.get('series')
        next_serial_no = 1  # Default to 1 if no existing serial number

        if series:
            last_serial = Table_Voucher.objects.filter(Series=series).order_by('-VoucherNo').first()
            if last_serial:
                next_serial_no = last_serial.VoucherNo + 1

        return JsonResponse({'next_serial_no': next_serial_no})
    

class VoucherConfigurationTable(LoginRequiredMixin, ListView):
    model = VoucherConfiguration
    template_name = 'web/accounts/voucher-configuration/voucher_search.html'
    context_object_name = "voucherconfiguration"


# - ACCOUNT MASTER

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Table_Accountsmaster
from .forms import AccountMasterForm
import json

class AccountMasterView(LoginRequiredMixin, CreateView):
    model = Table_Accountsmaster
    form_class = AccountMasterForm
    template_name = 'web/accounts/account-master/acc-master.html'
    success_url = reverse_lazy("web:acc_master")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        opbalance = form.cleaned_data.get('opbalance', 0)  # Get the opening balance
        debitcredit = form.cleaned_data.get('debitcredit')  # Get the debit/credit choice
        
        # Set opbalance and currentbalance based on debitcredit selection
        if debitcredit == 'Debit':
            form.instance.opbalance = abs(opbalance)  # Ensure positive
            form.instance.currentbalance = abs(opbalance)  # Ensure positive
        elif debitcredit == 'Credit':
            form.instance.opbalance = -abs(opbalance)  # Ensure negative
            form.instance.currentbalance = -abs(opbalance)  # Ensure negative
        
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Account created successfully!')
            return response
        except IntegrityError:
            form.add_error('head', 'This head already exists for this user. Please choose a different one.')
            return self.form_invalid(form)



from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Table_Accountsmaster  # Adjust the import according to your structure

from django.http import JsonResponse

class AccountmMasterUserView(LoginRequiredMixin, ListView):
    model = Table_Accountsmaster
    template_name = "web/accounts/account-master/acc_master_list.html"
    context_object_name = "userlists"

    def get_queryset(self):
        # Get all records for the logged-in user
        queryset = self.model.objects.filter(user=self.request.user)
        search_query = self.request.GET.get('search')
        
        # Filter queryset if search_query exists
        if search_query:
            queryset = queryset.filter(head__icontains=search_query)
        
        return queryset

    def get(self, request, *args, **kwargs):
        # Check if the request is AJAX by inspecting the HTTP headers
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            queryset = self.get_queryset()
            results = [{
                'account_code': userlist.account_code,
                'head': userlist.head,
                'group': userlist.group,
                'category': userlist.category,
                'mobile': userlist.mobile,
                'slug': userlist.slug,
                'get_absolute_url': userlist.get_absolute_url()
            } for userlist in queryset]
            return JsonResponse({'results': results})  # Return JSON response

        return super().get(request, *args, **kwargs)  # Default behavior for non-AJAX requests



class AccountMasterDetailView(DetailView):
    model = Table_Accountsmaster
    template_name = 'web/accounts/account-master/acc_master_detail.html'  # Ensure this template exists

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        user = self.request.user
        
        # Fetch the account associated with the current user using get_object_or_404
        return get_object_or_404(Table_Accountsmaster, slug=slug, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["userlist"] = self.get_object()
        return context


class EditAccountmMasterUserView(LoginRequiredMixin, UpdateView):
    model = Table_Accountsmaster
    form_class = AccountMasterForm
    template_name = 'web/accounts/account-master/acc-master.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        user = self.request.user
        return get_object_or_404(Table_Accountsmaster, slug=slug, user=user)

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        opbalance = form.cleaned_data.get('opbalance', 0)  # Get the opening balance
        debitcredit = form.cleaned_data.get('debitcredit')  # Get the debit/credit choice
        
        # Set opbalance and currentbalance based on debitcredit selection
        if debitcredit == 'Debit':
            form.instance.opbalance = abs(opbalance)  # Ensure positive
            form.instance.currentbalance = abs(opbalance)  # Ensure positive
        elif debitcredit == 'Credit':
            form.instance.opbalance = -abs(opbalance)  # Ensure negative
            form.instance.currentbalance = -abs(opbalance)  # Ensure negative

        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Account updated successfully!')
            return response
        except IntegrityError:
            form.add_error('head', 'This head already exists for this user. Please choose a different one.')
            return self.form_invalid(form)

    def get_success_url(self):
        if self.object and self.object.slug:
            return reverse_lazy('web:account_master_detail', kwargs={'slug': self.object.slug})
        else:
            return reverse_lazy('web:account_master_list')  # Redirect to a list or other page



class DeleteAccountmMasterUserView(DeleteView):
    model = Table_Accountsmaster
    template_name = 'web/accounts/account-master/acc-master.html'
    success_url = reverse_lazy('web:acc_master')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return JsonResponse({'message': 'Deleted successfully'})

    def get(self, request, *args, **kwargs):
        # Ensure that the view only handles DELETE requests
        return JsonResponse({'error': 'GET method not allowed'}, status=405) 
    
# - COMPANY MASTER


from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import Table_Companydetailsmaster
from .forms import ComapnyDetailsMasterForm
from django.core.exceptions import ValidationError


class CompanyDetailsMasterView(LoginRequiredMixin, CreateView):
    model = Table_Companydetailsmaster
    form_class = ComapnyDetailsMasterForm
    template_name = "web/accounts/company-master/companydetailsmaster.html"
    success_url = reverse_lazy("web:company_details_master")
    success_message = "Company Details Created Successfully"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, self.success_message, extra_tags="form_submit")
            return response
        except ValidationError as e:
            messages.error(self.request, str(e), extra_tags="form_error")
            return self.form_invalid(form)





class CompanyMasterUserView(LoginRequiredMixin, ListView):
    model = Table_Companydetailsmaster
    template_name = "web/accounts/company-master/companymaster_list.html"
    context_object_name = "companylists"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(head__icontains=search_query)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            qs_json = serializers.serialize("json", self.get_queryset())
            return JsonResponse({"results": json.loads(qs_json)}, safe=False)
        else:
            return super(CompanyMasterUserView, self).render_to_response(
                context, **response_kwargs
            )


class CompanyMasterDetailView(LoginRequiredMixin, DetailView):
    model = Table_Companydetailsmaster
    template_name = "web/accounts/company-master/companymaster_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        companylists = get_object_or_404(Table_Companydetailsmaster, slug=slug)
        context["companylist"] = companylists
        return context


class DeletecompanymMasterUserView(LoginRequiredMixin, DeleteView):
    model = Table_Companydetailsmaster
    success_url = reverse_lazy("web:company_details_master")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(
            request, "Account Deleted Successfully", extra_tags="form_delete"
        )
        return HttpResponseRedirect(success_url)


from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.contrib import messages
from django.db import IntegrityError
from .models import Table_Companydetailsmaster
from .forms import ComapnyDetailsMasterForm

class EditCompanyMasterUserView(LoginRequiredMixin, UpdateView):
    model = Table_Companydetailsmaster
    form_class = ComapnyDetailsMasterForm
    template_name = "web/accounts/company-master/companydetailsmaster.html"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Account edited successfully!")
            return response
        except IntegrityError:
            form.add_error(
                "company_id", "This Company ID already exists. Please choose a different one."
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "web:companymaster_detail", kwargs={"slug": self.object.slug}
        )


# - RECEIPT 


class EnterAmountView(LoginRequiredMixin, View):
    template_name = 'web/accounts/receipt/receipt.html'

    def get(self, request, *args, **kwargs):
        vouchers = VoucherConfiguration.objects.filter(category='receipt')
        next_serial_numbers = {voucher.series: voucher.serial_no for voucher in vouchers}

        account_masters = Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank'])
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank'])

        table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
            account_master__category__in=['Bank', 'Cashbook']
        )

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': account_masters,
            'wallet': Wallet.objects.first(),
            'head_accounts': head_accounts,
            'next_serial_numbers': next_serial_numbers,
            'selected_series': None,
            'next_voucher_no': None,
            'table_acntchildren': table_acntchildren,
            'user_id': request.user.id,
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('Series')
            vdate = request.POST.get('Vdate')
            headcode = request.POST.get('Headcode')
            user_id = request.user.id
            fy_code = '2024-2025'
            coid = 'C'
            branch_id = '1'
    
            accountcodes = request.POST.getlist('Accountcode[]')
            narrations = request.POST.getlist('Narration[]')
            vtypes = request.POST.getlist('VType[]')
            payments = request.POST.getlist('payment[]')
    
            if not (len(accountcodes) == len(narrations) == len(vtypes) == len(payments)):
                raise ValueError("Mismatched input lengths in form data.")
    
            total_amount = sum(float(payment) for payment in payments)
    
            voucher_config = VoucherConfiguration.objects.get(series=series, category='receipt')
            current_serial_no = int(voucher_config.serial_no)
            voucher_no = current_serial_no
    
            with transaction.atomic():
                for accountcode, narration, vtype, payment in zip(accountcodes, narrations, vtypes, payments):
                    # Create voucher entry
                    Table_Voucher.objects.create(
                        Series=series,
                        VoucherNo=voucher_no,
                        Vdate=vdate,
                        Accountcode=accountcode,
                        Headcode=headcode,
                        payment=payment,
                        VAmount=total_amount,
                        VType=vtype,
                        Narration=narration,
                        CStatus='R',
                        UserID=user_id,
                        FYCode=fy_code,
                        Coid=coid,
                        Branch_ID=branch_id
                    )
    
                    # Update the current balance for Table_Acntchild
                    try:
                        acnt_child = Table_Acntchild.objects.get(account_code=accountcode)
                        current_balance = float(acnt_child.current_balance or 0)
                        payment_amount = float(payment)
                        new_balance = current_balance - payment_amount
    
                        acnt_child.current_balance = str(new_balance)
                        acnt_child.save()
                    except Table_Acntchild.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Acntchild.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode}: {e}")
    
                    # Update the current balance for Table_Accountsmaster
                    try:
                        account_master = Table_Accountsmaster.objects.get(account_code=accountcode)
                        current_balance_master = float(account_master.currentbalance or 0)
                        new_balance_master = current_balance_master - float(payment)
    
                        account_master.currentbalance = str(new_balance_master)
                        account_master.save()
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode} in Table_Accountsmaster: {e}")
    
                # Only update the selected account
                selected_account_code = request.POST.get('Headcode')
                # In the EnterAmountView post method

                # Update the current balance for Table_Accountsmaster (Head accounts)
                if selected_account_code:
                    try:
                        selected_account_master = Table_Accountsmaster.objects.get(account_code=selected_account_code)
                        current_balance_master = float(selected_account_master.currentbalance or 0)
                        new_balance_master = current_balance_master + total_amount

                        selected_account_master.currentbalance = str(new_balance_master)
                        selected_account_master.save()
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Selected account code {selected_account_code} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for selected account code {selected_account_code}: {e}")

    
                voucher_config.serial_no = voucher_no + 1
                voucher_config.save()
    
            next_serial_numbers = {
                voucher.series: str(voucher_config.serial_no)
                for voucher in VoucherConfiguration.objects.filter(category='receipt')
            }
    
            return render(request, self.template_name, {
                'success': "Voucher saved successfully!",
                'vouchers': VoucherConfiguration.objects.filter(category='receipt'),
                'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                'wallet': Wallet.objects.first(),
                'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                'next_serial_numbers': next_serial_numbers,
                'selected_series': series,
                'next_voucher_no': next_serial_numbers.get(series),
                'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                    account_master__category__in=['Bank', 'Cashbook']
                ),
                'user_id': request.user.id,
            })
        except Exception as e:
            print(f"Error: {e}")
            # If there's an error, still provide the necessary context
            next_serial_numbers = {
                voucher.series: str(voucher_config.serial_no)
                for voucher in VoucherConfiguration.objects.filter(category='receipt')
            }
            
            return render(request, self.template_name, {
                'error': str(e),
                'vouchers': VoucherConfiguration.objects.filter(category='receipt'),
                'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                'wallet': Wallet.objects.first(),
                'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                'next_serial_numbers': next_serial_numbers,
                'selected_series': series,
                'next_voucher_no': next_serial_numbers.get(series),
                'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                    account_master__category__in=['Bank', 'Cashbook']
                ),
                'user_id': request.user.id,
            })
        
        
class EditReceiptView(LoginRequiredMixin, View):
    template_name = 'web/accounts/receipt/edit_receipt.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series')
        voucher_no = request.GET.get('VoucherNo')

        # Fetch necessary data
        vouchers = VoucherConfiguration.objects.filter(category='receipt')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank'])
        wallet = Wallet.objects.first()
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank'])
        table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
            account_master__category__in=['Bank', 'Cashbook']
        )

        # Fetch voucher entries for the given series and voucher number
        voucher_entries = Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no)

        if not voucher_entries:
            return render(request, 'web/accounts/receipt/receipt_modify.html', {
                'vouchers': vouchers,
                'accountmas': accountmas,
                'wallet': wallet,
                'head_accounts': head_accounts,
                'table_acntchildren': table_acntchildren,
                'voucher_entries': [],
                'user_id': request.user.id,
                'error_message': 'This combination of Series and Voucher No does not exist.',
                'redirect_url': reverse('web:receipt_modify')  # Replace with the correct URL name
            })

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'wallet': wallet,
            'head_accounts': head_accounts,
            'table_acntchildren': table_acntchildren,
            'voucher_entries': voucher_entries,
            'user_id': request.user.id,
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('Series')
            vdate = request.POST.get('Vdate')
            headcode = request.POST.get('Headcode')
            user_id = request.user.id
            fy_code = '2024-2025'
            coid = 'C'
            branch_id = '1'
    
            accountcodes = request.POST.getlist('Accountcode[]')
            narrations = request.POST.getlist('Narration[]')
            vtypes = request.POST.getlist('VType[]')
            payments = request.POST.getlist('payment[]')
    
            if not (len(accountcodes) == len(narrations) == len(vtypes) == len(payments)):
                raise ValueError("Mismatched input lengths in form data.")
    
            total_amount = sum(float(payment) for payment in payments)
            voucher_no = request.POST.get('VoucherNo')
    
            # Use a transaction to ensure atomic operations
            with transaction.atomic():
                # Fetch and revert existing voucher entries
                voucher_entries = Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no)
                old_total_amount = 0
                for entry in voucher_entries:
                    account_code = entry.Accountcode
                    payment_amount = float(entry.payment)
                    old_total_amount += payment_amount
    
                    # Revert the old payment amount from Table_Acntchild
                    try:
                        acnt_child = Table_Acntchild.objects.get(account_code=account_code)
                        current_balance = float(acnt_child.current_balance or 0)
                        new_balance = current_balance + payment_amount  # Add back the old amount
                        acnt_child.current_balance = str(new_balance)
                        acnt_child.save()
                    except Table_Acntchild.DoesNotExist:
                        print(f"Account code {account_code} not found in Table_Acntchild.")
                    except Exception as e:
                        print(f"Error reverting balance for account code {account_code}: {e}")
    
                    # Revert the old payment amount from Table_Accountsmaster
                    try:
                        account_master = Table_Accountsmaster.objects.get(account_code=account_code)
                        current_balance_master = float(account_master.currentbalance or 0)
                        new_balance_master = current_balance_master + payment_amount  # Add back the old amount
                        account_master.currentbalance = str(new_balance_master)
                        account_master.save()
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account code {account_code} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error reverting balance for account code {account_code} in Table_Accountsmaster: {e}")
    
                # Delete old voucher entries after reverting balances
                voucher_entries.delete()
    
                # Create new voucher entries with updated balances
                for accountcode, narration, vtype, payment in zip(accountcodes, narrations, vtypes, payments):
                    Table_Voucher.objects.create(
                        Series=series,
                        VoucherNo=voucher_no,
                        Vdate=vdate,
                        Accountcode=accountcode,
                        Headcode=headcode,
                        payment=payment,
                        VAmount=total_amount,
                        VType=vtype,
                        Narration=narration,
                        CStatus='R',
                        UserID=user_id,
                        FYCode=fy_code,
                        Coid=coid,
                        Branch_ID=branch_id
                    )
    
                    # Update the current balance for Table_Acntchild
                    try:
                        acnt_child = Table_Acntchild.objects.get(account_code=accountcode)
                        current_balance = float(acnt_child.current_balance or 0)
                        new_balance = current_balance - float(payment)  # Subtract the new amount
                        acnt_child.current_balance = str(new_balance)
                        acnt_child.save()
                    except Table_Acntchild.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Acntchild.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode}: {e}")
    
                    # Update the current balance for Table_Accountsmaster
                    try:
                        account_master = Table_Accountsmaster.objects.get(account_code=accountcode)
                        current_balance_master = float(account_master.currentbalance or 0)
                        new_balance_master = current_balance_master - float(payment)  # Subtract the new amount
                        account_master.currentbalance = str(new_balance_master)
                        account_master.save()
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode} in Table_Accountsmaster: {e}")
    
                # Update the balance of the selected head account
                if headcode:
                    try:
                        selected_account_master = Table_Accountsmaster.objects.get(account_code=headcode)
                        current_balance_master = float(selected_account_master.currentbalance or 0)
                        new_balance_master = current_balance_master + total_amount - old_total_amount
    
                        selected_account_master.currentbalance = str(new_balance_master)
                        selected_account_master.save()
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Selected account code {headcode} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for selected account code {headcode}: {e}")
    
                return render(request, self.template_name, {
                    'success': "Receipt updated successfully!",
                    'vouchers': VoucherConfiguration.objects.filter(category='receipt'),
                    'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                    'wallet': Wallet.objects.first(),
                    'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                    'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                        account_master__category__in=['Bank', 'Cashbook']
                    ),
                    'user_id': request.user.id,
                    'redirect_url': reverse('web:receipt_modify')  # Replace with the correct URL name
                })
        except Exception as e:
            print(f"Error: {e}")
            # Handle errors appropriately
            return render(request, self.template_name, {
                'error': str(e),
                'vouchers': VoucherConfiguration.objects.filter(category='receipt'),
                'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                'wallet': Wallet.objects.first(),
                'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                    account_master__category__in=['Bank', 'Cashbook']
                ),
                'user_id': request.user.id,
                'redirect_url': reverse('web:receipt')  # Replace with the correct URL name
            })
    








   

class SearchReceiptView(LoginRequiredMixin, View):
    template_name = 'web/accounts/receipt/receipt_modify.html'

    def get(self, request, *args, **kwargs):
        vouchers = VoucherConfiguration.objects.filter(category='receipt')
        return render(request, self.template_name, {'vouchers': vouchers})
    
    
class ReceiptDetailView(View):
    template_name = 'web/accounts/receipt/table-details.html'

    def get(self, request, voucher_id, *args, **kwargs):
        voucher = get_object_or_404(Table_Voucher, id=voucher_id)
        return render(request, self.template_name, {
            'voucher': voucher,
        })


class ReceiptListTable(LoginRequiredMixin, ListView):
    model = Table_Voucher
    template_name = 'web/accounts/receipt/receipt_list.html'
    context_object_name = "vouchers"

    def get_queryset(self):
        # Get all series related to the receipt category from VoucherConfiguration
        receipt_series = VoucherConfiguration.objects.filter(category='receipt').values_list('series', flat=True)
        
        # Filter Table_Voucher based on the series related to the receipt category and CStatus being 'R'
        return Table_Voucher.objects.filter(Series__in=receipt_series, CStatus='R')
    

# - PAYMENT

from django.db import transaction
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import VoucherConfiguration, Table_Acntchild, Table_Accountsmaster, Table_Voucher

class PaymentEnterAmountView(LoginRequiredMixin, View):
    template_name = 'web/accounts/payment/payment.html'

    def get(self, request, *args, **kwargs):
        # Get relevant data
        vouchers = VoucherConfiguration.objects.filter(category='payment')
        next_serial_numbers = {voucher.series: voucher.serial_no for voucher in vouchers}

        account_masters = Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank'])
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank'])

        table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
            account_master__category__in=['Bank', 'Cashbook']
        )

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': account_masters,
            'head_accounts': head_accounts,
            'next_serial_numbers': next_serial_numbers,
            'table_acntchildren': table_acntchildren,
            'user_id': request.user.id,
        })

    def update_current_balance(self, account_code, payment, increase=True):
        try:
            acnt_child = Table_Acntchild.objects.get(account_code=account_code)
            current_balance = float(acnt_child.current_balance or 0)
            payment_amount = float(payment)
            new_balance = current_balance + payment_amount if increase else current_balance - payment_amount
            acnt_child.current_balance = str(new_balance)
            acnt_child.save()
        except Table_Acntchild.DoesNotExist:
            print(f"Account code {account_code} not found in Table_Acntchild.")
        except Exception as e:
            print(f"Error updating balance for account code {account_code}: {e}")

        try:
            account_master = Table_Accountsmaster.objects.get(account_code=account_code)
            current_balance_master = float(account_master.currentbalance or 0)
            # Update balance with appropriate adjustment for head accounts
            if account_master.category in ['Cashbook', 'Bank']:
                new_balance_master = current_balance_master - payment_amount if increase else current_balance_master - payment_amount
            else:
                new_balance_master = current_balance_master - payment_amount if not increase else current_balance_master + payment_amount
            account_master.currentbalance = str(new_balance_master)
            account_master.save()
        except Table_Accountsmaster.DoesNotExist:
            print(f"Account code {account_code} not found in Table_Accountsmaster.")
        except Exception as e:
            print(f"Error updating balance for account code {account_code} in Table_Accountsmaster: {e}")


    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('Series')
            vdate = request.POST.get('Vdate')
            headcode = request.POST.get('Headcode')
            user_id = request.user.id
            fy_code = '2024-2025'
            coid = 'C'
            branch_id = '1'

            accountcodes = request.POST.getlist('Accountcode[]')
            narrations = request.POST.getlist('Narration[]')
            vtypes = request.POST.getlist('VType[]')
            payments = request.POST.getlist('payment[]')

            if not (len(accountcodes) == len(narrations) == len(vtypes) == len(payments)):
                raise ValueError("Mismatched input lengths in form data.")

            total_amount = sum(float(payment) for payment in payments)

            voucher_config = VoucherConfiguration.objects.get(series=series, category='payment')
            current_serial_no = int(voucher_config.serial_no)
            voucher_no = current_serial_no

            with transaction.atomic():
                for accountcode, narration, vtype, payment in zip(accountcodes, narrations, vtypes, payments):
                    # Create voucher entry
                    Table_Voucher.objects.create(
                        Series=series,
                        VoucherNo=voucher_no,
                        Vdate=vdate,
                        Accountcode=accountcode,
                        Headcode=headcode,
                        payment=payment,
                        VAmount=total_amount,
                        VType=vtype,
                        Narration=narration,
                        CStatus='P',
                        UserID=user_id,
                        FYCode=fy_code,
                        Coid=coid,
                        Branch_ID=branch_id
                    )

                    # Update the current balance for each account
                    self.update_current_balance(accountcode, payment)

                # Only update the selected account
                selected_account_code = request.POST.get('Headcode')
                if selected_account_code:
                    self.update_current_balance(selected_account_code, total_amount)

                voucher_config.serial_no = voucher_no + 1
                voucher_config.save()

            next_serial_numbers = {
                voucher.series: str(voucher_config.serial_no)
                for voucher in VoucherConfiguration.objects.filter(category='payment')
            }

            return render(request, self.template_name, {
                'success': "Payment voucher saved successfully!",
                'vouchers': VoucherConfiguration.objects.filter(category='payment'),
                'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                'next_serial_numbers': next_serial_numbers,
                'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                    account_master__category__in=['Bank', 'Cashbook']
                ),
                'user_id': request.user.id,
            })
        except Exception as e:
            print(f"Error: {e}")
            next_serial_numbers = {
                voucher.series: str(voucher_config.serial_no)
                for voucher in VoucherConfiguration.objects.filter(category='payment')
            }
            return render(request, self.template_name, {
                'error': str(e),
                'vouchers': VoucherConfiguration.objects.filter(category='payment'),
                'accountmas': Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank']),
                'head_accounts': Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank']),
                'next_serial_numbers': next_serial_numbers,
                'table_acntchildren': Table_Acntchild.objects.select_related('account_master').filter(
                    account_master__category__in=['Bank', 'Cashbook']
                ),
                'user_id': request.user.id,
            })








from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from .models import VoucherConfiguration, Table_Voucher, Table_Accountsmaster, Table_Acntchild, Wallet
from django.urls import reverse

class EditPaymentView(LoginRequiredMixin, View):
    template_name = 'web/accounts/payment/edit_payment.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series')
        voucher_no = request.GET.get('VoucherNo')

        # Fetch necessary data
        vouchers = VoucherConfiguration.objects.filter(category='payment')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank'])
        wallet = Wallet.objects.first()
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank'])
        table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
            account_master__category__in=['Bank', 'Cashbook']
        )

        # Fetch voucher entries for the given series and voucher number
        voucher_entries = Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no)

        if not voucher_entries:
            # If voucher entries do not exist, display SweetAlert error message
            return render(request, 'web/accounts/payment/payment_modify.html', {
                'vouchers': vouchers,
                'accountmas': accountmas,
                'wallet': wallet,
                'head_accounts': head_accounts,
                'table_acntchildren': table_acntchildren,
                'voucher_entries': [],
                'user_id': request.user.id,
                'error_message': 'This combination of Series and Voucher No does not exist.',
                'redirect_url': reverse('web:payment_modify')  # Replace with the correct URL name
            })

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'wallet': wallet,
            'head_accounts': head_accounts,
            'table_acntchildren': table_acntchildren,
            'voucher_entries': voucher_entries,
            'user_id': request.user.id,
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('Series')
            vdate = request.POST.get('Vdate')
            headcode = request.POST.get('Headcode')
            user_id = request.user.id
            fy_code = '2024-2025'
            coid = 'C'
            branch_id = '1'
    
            accountcodes = request.POST.getlist('Accountcode[]')
            narrations = request.POST.getlist('Narration[]')
            vtypes = request.POST.getlist('VType[]')
            payments = request.POST.getlist('payment[]')
            voucher_no = request.POST.get('VoucherNo')
    
            # Ensure all lists are of the same length
            if not (len(accountcodes) == len(narrations) == len(vtypes) == len(payments)):
                raise ValueError("Mismatched input lengths in form data.")
    
            # Validate that all payments except those related to head_accounts are positive
            for payment, accountcode in zip(payments, accountcodes):
                if Table_Accountsmaster.objects.filter(account_code=accountcode).exclude(category__in=['Cashbook', 'Bank']).exists():
                    if float(payment) < 0:
                        raise ValueError(f"Payment for account code {accountcode} must be positive.")
    
            # Calculate the new total amount
            new_total_amount = sum(float(payment) for payment in payments)
    
            with transaction.atomic():
                # Fetch existing entries to get old amounts and account codes
                old_entries = Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no)
    
                # Calculate the old total amount
                old_total_amount = sum(float(entry.payment) for entry in old_entries)
    
                # Revert previous balances before updating
                for old_entry in old_entries:
                    accountcode = old_entry.Accountcode
                    old_payment = old_entry.payment
                    try:
                        account_master = Table_Accountsmaster.objects.get(account_code=accountcode)
                        current_balance_master = float(account_master.currentbalance or 0)
                        updated_balance_master = current_balance_master - float(old_payment)  # Revert balance
                        account_master.currentbalance = str(updated_balance_master)
                        account_master.save()
    
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode} in Table_Accountsmaster: {e}")
    
                # Delete old entries
                old_entries.delete()
    
                # Update or create new entries and adjust balances
                for accountcode, narration, vtype, payment in zip(accountcodes, narrations, vtypes, payments):
                    Table_Voucher.objects.create(
                        Series=series,
                        VoucherNo=voucher_no,
                        Vdate=vdate,
                        Accountcode=accountcode,
                        Headcode=headcode,
                        payment=payment,
                        VAmount=new_total_amount,  # Save the total amount
                        VType=vtype,
                        Narration=narration,
                        CStatus='P',
                        UserID=user_id,
                        FYCode=fy_code,
                        Coid=coid,
                        Branch_ID=branch_id
                    )
    
                    # Update the balance in Table_Accountsmaster
                    try:
                        account_master = Table_Accountsmaster.objects.get(account_code=accountcode)
                        current_balance_master = float(account_master.currentbalance or 0)
                        updated_balance_master = current_balance_master + float(payment)  # Add new payment
                        account_master.currentbalance = str(updated_balance_master)
                        account_master.save()
    
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account code {accountcode} not found in Table_Accountsmaster.")
                    except Exception as e:
                        print(f"Error updating balance for account code {accountcode} in Table_Accountsmaster: {e}")
    
                # Update the balance for head_accounts by adding the difference between the new and old total amount
                try:
                    head_account = Table_Accountsmaster.objects.get(account_code=headcode)
                    current_balance_head = float(head_account.currentbalance or 0)
                    difference = new_total_amount - old_total_amount
                    updated_balance_head = current_balance_head - difference
                    head_account.currentbalance = str(updated_balance_head)
                    head_account.save()
    
                except Table_Accountsmaster.DoesNotExist:
                    print(f"Head account code {headcode} not found in Table_Accountsmaster.")
                except Exception as e:
                    print(f"Error updating balance for head account code {headcode} in Table_Accountsmaster: {e}")
    
                # Update the serial number in VoucherConfiguration for the next use if not editing
                if not voucher_no:
                    voucher_config = VoucherConfiguration.objects.get(series=series, category='payment')
                    voucher_config.serial_no += 1
                    voucher_config.save()
    
            print("Payment saved successfully!")
            return redirect('web:payment')  # Redirect to payment modify page after saving
    
        except Exception as e:
            print("Error saving payment: ", e)
    
            # Fetch necessary data to repopulate the form
            vouchers = VoucherConfiguration.objects.filter(category='payment')
            accountmas = Table_Accountsmaster.objects.filter(category__in=['Cashbook', 'Bank'])
            wallet = Wallet.objects.first()
            head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Cashbook', 'Bank'])
            table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
                account_master__category__in=['Bank', 'Cashbook']
            )
    
            return render(request, self.template_name, {
                'error_message': str(e),
                'vouchers': vouchers,
                'accountmas': accountmas,
                'wallet': wallet,
                'head_accounts': head_accounts,
                'table_acntchildren': table_acntchildren,
                'voucher_entries': Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no),
                'user_id': request.user.id,
            })

    








        
    
class SearchPaymentView(LoginRequiredMixin, View):
    template_name = 'web/accounts/payment/payment_modify.html'

    def get(self, request, *args, **kwargs):
        vouchers = VoucherConfiguration.objects.filter(category='payment')
        return render(request, self.template_name, {'vouchers': vouchers})
    

class ModifyPaymentTableView(TemplateView):
    template_name = 'web/accounts/payment/payment_modify.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['series_options'] = VoucherConfiguration.objects.filter(category='payment').values('series')
        return context

    def post(self, request, *args, **kwargs):
        series = request.POST.get('series')
        voucher_no = request.POST.get('voucher_no')  # Change from serial_no to VoucherNo

        if series and voucher_no:
            # Check if the voucher number exists
            if Table_Voucher.objects.filter(Series=series, VoucherNo=voucher_no, CStatus='R').exists():
                return redirect(reverse('web:account_debit_note', kwargs={'series': series, 'voucher_no': voucher_no}))
            else:
                context = self.get_context_data(**kwargs)
                context['error'] = 'This voucher number does not exist or does not match the criteria.'
                return render(request, self.template_name, context)
        
        context = self.get_context_data(**kwargs)
        context['error'] = 'Please enter both series and voucher number.'
        return render(request, self.template_name, context)


class PaymentListTable(LoginRequiredMixin, ListView):
    model = Table_Voucher
    template_name = 'web/accounts/payment/payment_list.html'
    context_object_name = "vouchers"

    def get_queryset(self):
        # Get all series related to the payment category from VoucherConfiguration
        payment_series = VoucherConfiguration.objects.filter(category='payment').values_list('series', flat=True)
        
        # Filter Table_Voucher based on the series related to the payment category and CStatus being 'R'
        return Table_Voucher.objects.filter(Series__in=payment_series, CStatus='P')


# - DEBIT NOTES

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Table_DrCrNote, VoucherConfiguration, Table_Accountsmaster

class AccountDebitNoteView(TemplateView):
    template_name = 'web/accounts/debit-note/debit-note.html'
    success_url = reverse_lazy('web:account_debit_note')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.kwargs.get('series')
        serial_no = self.kwargs.get('serial_no')
        
        logger.debug(f'Getting context data for series: {series}, serial_no: {serial_no}')

        context['series_options'] = VoucherConfiguration.objects.filter(category='Debit Note').values('series', 'serial_no')
        excluded_categories = ['Bank', 'Cashbook']
        head_options = Table_Accountsmaster.objects.exclude(category__in=excluded_categories).values('head', 'account_code')
        context['head_options'] = head_options
        context['drcrnotes'] = Table_DrCrNote.objects.filter(ntype='D')
        context['series'] = series
        context['serial_no'] = serial_no
    
        if series and serial_no:
            matched_notes = Table_DrCrNote.objects.filter(series=series, noteno=serial_no, ntype='D')
            logger.debug(f'Matched notes: {matched_notes}')

            if matched_notes.exists():
                matched_note_dr = matched_notes.filter(dramount__gt=0).first()
                matched_note_cr = matched_notes.filter(cramount__gt=0).first()
    
                if matched_note_dr:
                    matched_note_dr_head = Table_Accountsmaster.objects.filter(account_code=matched_note_dr.accountcode).first()
                    if matched_note_dr_head:
                        matched_note_dr.head = matched_note_dr_head.head
                    matched_note_dr.ndate = matched_note_dr.ndate.strftime('%Y-%m-%d')
                    context['matched_note_dr'] = matched_note_dr
    
                if matched_note_cr:
                    matched_note_cr_head = Table_Accountsmaster.objects.filter(account_code=matched_note_cr.accountcode).first()
                    if matched_note_cr_head:
                        matched_note_cr.head = matched_note_cr_head.head
                    context['matched_note_cr'] = matched_note_cr
    
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context['company_name'] = company_details.companyname
            context['address1'] = company_details.address1
            context['address2'] = company_details.address2
            context['phoneno'] = company_details.phoneno
    
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        series = request.POST.get('series')
        serial_no = request.POST.get('serial_no')
        date = request.POST.get('date')
        head1 = request.POST.get('head1')
        narration1 = request.POST.get('narration1')
        debit1_str = request.POST.get('debit1', '0')
        debit1 = float(debit1_str) if debit1_str else 0.0  # Convert to float with default value
        head2 = request.POST.get('head2')
        narration2 = request.POST.get('narration2')
        credit2_str = request.POST.get('credit2', '0')
        credit2 = float(credit2_str) if credit2_str else 0.0  # Convert to float with default value
    
        try:
            if series and serial_no:
                matched_notes = Table_DrCrNote.objects.filter(series=series, noteno=serial_no)
                if matched_notes.exists():
                    # Update existing debit and credit notes
                    dr_note = matched_notes.filter(dramount__gt=0).first()
                    cr_note = matched_notes.filter(cramount__gt=0).first()
    
                    # Update the current balance before updating the note
                    if dr_note:
                        self.update_account_balance(dr_note.accountcode, -float(dr_note.dramount))
                    if cr_note:
                        self.update_account_balance(cr_note.accountcode, float(cr_note.cramount))
    
                    # Update the note details
                    if dr_note:
                        dr_note.ndate = date
                        dr_note.accountcode = head1  # Debit account
                        dr_note.narration = narration1
                        dr_note.dramount = debit1
                        dr_note.save()
                        # Update the Account_Master table for debit
                        self.update_account_balance(head1, debit1)
                    if cr_note:
                        cr_note.ndate = date
                        cr_note.accountcode = head2  # Credit account
                        cr_note.narration = narration2
                        cr_note.cramount = credit2
                        cr_note.save()
                        # Update the Account_Master table for credit
                        self.update_account_balance(head2, -credit2)
    
                    messages.success(request, 'Debit note updated successfully.')
                else:
                    # Create new entries if no existing notes are matched
                    self.create_new_entries(request, series, date, head1, narration1, debit1, head2, narration2, credit2)
    
            else:
                # Create new entries if series and serial_no are not provided
                self.create_new_entries(request, series, date, head1, narration1, debit1, head2, narration2, credit2)
    
            return redirect(self.success_url)
    
        except Exception as e:
            messages.error(request, f'Failed to save debit note: {str(e)}')
            return redirect(self.success_url)
    

    def create_new_entries(self, request, series, date, head1, narration1, debit1, head2, narration2, credit2):
        voucher_config = VoucherConfiguration.objects.filter(series=series, category='Debit Note').first()
    
        if not voucher_config:
            messages.error(request, 'Invalid series for Debit Note.')
            return redirect(self.success_url)
    
        current_serial_no = voucher_config.serial_no
        next_serial_no = current_serial_no + 1
    
        voucher_config.serial_no = next_serial_no
        voucher_config.save()
    
        coid_entry = Table_companyDetailschild.objects.first()
        fycode_entry = Table_companyDetailschild.objects.first()
        coid = coid_entry.company_id if coid_entry else 'C'
        fycode = fycode_entry.fycode if fycode_entry else 'NON'
        user = request.user
    
        Table_DrCrNote.objects.create(
            series=series,
            ndate=date,
            noteno=current_serial_no,
            accountcode=head1,
            narration=narration1,
            dramount=debit1,
            cramount='0',
            ntype='D',
            userid=user.username,  # Correct field name
            coid=coid,
            fycode=fycode,
            brid='1'
        )
    
        Table_DrCrNote.objects.create(
            series=series,
            ndate=date,
            noteno=current_serial_no,
            accountcode=head2,
            narration=narration2,
            dramount='0',
            cramount=credit2,
            ntype='D',
            userid=user.username,  # Correct field name
            coid=coid,
            fycode=fycode,
            brid='1'
        )
    
        self.update_account_balance(head1, debit1)
        self.update_account_balance(head2, -credit2)
    
        messages.success(request, 'Debit note created successfully.')
    

    def update_account_balance(self, account_code, amount):
        accounts = Table_Accountsmaster.objects.filter(account_code=account_code)
    
        if accounts.exists():
            for account in accounts:
                current_balance = float(account.currentbalance or 0)
                account.currentbalance = current_balance + amount
                account.save()
        else:
            raise ValueError(f"No accounts found with account code: {account_code}")








  


from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from .models import Table_DrCrNote

from django.shortcuts import get_object_or_404, Http404
from .models import Table_DrCrNote

class DeleteDebitNoteView(DeleteView):
    model = Table_DrCrNote
    success_url = reverse_lazy("web:account_debit_note")

    def get_object(self, queryset=None):
        pk1 = self.kwargs.get('pk1')
        pk2 = self.kwargs.get('pk2')

        # Fetch the object
        obj = Table_DrCrNote.objects.filter(id=pk1, noteno=pk2).first()
        if not obj:
            raise Http404("No Table_DrCrNote matches the given query.")
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Convert dramount and cramount to float before comparison
        dramount = float(self.object.dramount) if self.object.dramount else 0
        cramount = float(self.object.cramount) if self.object.cramount else 0

        # Update the account balance before deleting
        if dramount > 0:
            self.update_account_balance(self.object.accountcode, -dramount)
        elif cramount > 0:
            self.update_account_balance(self.object.accountcode, cramount)

        # Delete the object
        self.object.delete()

        # Optionally, handle the second object if needed
        obj2 = Table_DrCrNote.objects.filter(noteno=self.object.noteno).exclude(id=self.object.id).first()
        if obj2:
            dramount2 = float(obj2.dramount) if obj2.dramount else 0
            cramount2 = float(obj2.cramount) if obj2.cramount else 0
            
            if dramount2 > 0:
                self.update_account_balance(obj2.accountcode, -dramount2)
            elif cramount2 > 0:
                self.update_account_balance(obj2.accountcode, cramount2)
            obj2.delete()

        messages.success(request, "Debit note entry deleted successfully.")
        return redirect(success_url)

    def update_account_balance(self, account_code, amount):
        """Updates the current balance of the account(s) in Table_Accountsmaster."""
        accounts = Table_Accountsmaster.objects.filter(account_code=account_code)
    
        if accounts.exists():
            for account in accounts:
                current_balance = float(account.currentbalance or 0)
                account.currentbalance = current_balance + amount
                account.save()
        else:
            raise ValueError(f"No accounts found with account code: {account_code}")











from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from .models import Table_DrCrNote

class AccountDebitTableView(LoginRequiredMixin, ListView):
    model = Table_DrCrNote
    template_name = 'web/accounts/debit-note/debit-table.html'
    context_object_name = 'drcrnotes'

    def get_queryset(self):
        return Table_DrCrNote.objects.filter(ntype='D', userid=self.request.user.username)

          


class SearchDebitTableView(TemplateView):
    template_name = 'web/accounts/debit-note/debit-search-box.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['series_options'] = VoucherConfiguration.objects.filter(category='Debit Note').values('series')
        return context

    def post(self, request, *args, **kwargs):
        series = request.POST.get('series')
        serial_no = request.POST.get('serial_no')

        if series and serial_no:
            # Check if the serial number exists
            if Table_DrCrNote.objects.filter(series=series, noteno=serial_no, ntype='D').exists():
                return redirect(reverse('web:account_debit_note', kwargs={'series': series, 'serial_no': serial_no}))
            else:
                context = self.get_context_data(**kwargs)
                context['error'] = 'This serial number does not exist.'
                return render(request, self.template_name, context)
        
        context = self.get_context_data(**kwargs)
        context['error'] = 'Please enter both series and serial number.'
        return render(request, self.template_name, context)
    

class EditDebitTableView(LoginRequiredMixin, View):
    template_name = 'web/accounts/debit-note/edit-debit-note.html'


# - CREDIT NOTES

from django.shortcuts import redirect
from django.db import transaction
from django.contrib import messages
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from .models import Table_DrCrNote, Table_Accountsmaster, VoucherConfiguration, Table_companyDetailschild

import logging
from django.utils import timezone
from django.db import transaction


class AccountCreditNoteView(TemplateView):
    template_name = 'web/accounts/credit-note/credit-note.html'
    success_url = reverse_lazy('web:account_credit_note')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.kwargs.get('series')
        serial_no = self.kwargs.get('serial_no')
        
        logger.debug(f'Getting context data for series: {series}, serial_no: {serial_no}')

        context['series_options'] = VoucherConfiguration.objects.filter(category='Credit Note').values('series', 'serial_no')
        excluded_categories = ['Bank', 'Cashbook']
        head_options = Table_Accountsmaster.objects.exclude(category__in=excluded_categories).values('head', 'account_code')
        context['head_options'] = head_options
        context['drcrnotes'] = Table_DrCrNote.objects.filter(ntype='C')
        context['series'] = series
        context['serial_no'] = serial_no
    
        if series and serial_no:
            matched_notes = Table_DrCrNote.objects.filter(series=series, noteno=serial_no, ntype='C')
            logger.debug(f'Matched notes: {matched_notes}')

            if matched_notes.exists():
                matched_note_dr = matched_notes.filter(dramount__gt=0).first()
                matched_note_cr = matched_notes.filter(cramount__gt=0).first()
    
                if matched_note_dr:
                    matched_note_dr_head = Table_Accountsmaster.objects.filter(account_code=matched_note_dr.accountcode).first()
                    if matched_note_dr_head:
                        matched_note_dr.head = matched_note_dr_head.head
                    matched_note_dr.ndate = matched_note_dr.ndate.strftime('%Y-%m-%d')
                    context['matched_note_dr'] = matched_note_dr
    
                if matched_note_cr:
                    matched_note_cr_head = Table_Accountsmaster.objects.filter(account_code=matched_note_cr.accountcode).first()
                    if matched_note_cr_head:
                        matched_note_cr.head = matched_note_cr_head.head
                    context['matched_note_cr'] = matched_note_cr
    
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context['company_name'] = company_details.companyname
            context['address1'] = company_details.address1
            context['address2'] = company_details.address2
            context['phoneno'] = company_details.phoneno
    
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        series = request.POST.get('series')
        serial_no = request.POST.get('serial_no')
        date = request.POST.get('date')
        head1 = request.POST.get('head1')
        narration1 = request.POST.get('narration1')
        credit1_str = request.POST.get('credit1', '0')
        credit1 = float(credit1_str) if credit1_str else 0.0  # Convert to float with default value
        head2 = request.POST.get('head2')
        narration2 = request.POST.get('narration2')
        debit2_str = request.POST.get('debit2', '0')
        debit2 = float(debit2_str) if debit2_str else 0.0  # Convert to float with default value
    
        try:
            if series and serial_no:
                matched_notes = Table_DrCrNote.objects.filter(series=series, noteno=serial_no)
                if matched_notes.exists():
                    # Update existing debit and credit notes
                    dr_note = matched_notes.filter(dramount__gt=0).first()
                    cr_note = matched_notes.filter(cramount__gt=0).first()
    
                    # Update the current balance before updating the note
                    if dr_note:
                        self.update_account_balance(dr_note.accountcode, float(dr_note.dramount))
                    if cr_note:
                        self.update_account_balance(cr_note.accountcode, -float(cr_note.cramount))
    
                    # Update the note details
                    if dr_note:
                        dr_note.ndate = date
                        dr_note.accountcode = head1  # Updated to head2 for debit2
                        dr_note.narration = narration1
                        dr_note.dramount = credit1
                        dr_note.save()
                        # Update the Account_Master table for debit
                        self.update_account_balance(head1, -credit1)
                    if cr_note:
                        cr_note.ndate = date
                        cr_note.accountcode = head2  # Updated to head1 for credit1
                        cr_note.narration = narration2
                        cr_note.cramount = debit2
                        cr_note.save()
                        # Update the Account_Master table for credit
                        self.update_account_balance(head2, debit2)
    
                    messages.success(request, 'Credit note updated successfully.')
                else:
                    # Create new entries if no existing notes are matched
                    self.create_new_entries(request, series, date, head1, narration1, credit1, head2, narration2, debit2)
    
            else:
                # Create new entries if series and serial_no are not provided
                self.create_new_entries(request, series, date, head1, narration1, credit1, head2, narration2, debit2)
    
            return redirect(self.success_url)
    
        except Exception as e:
            messages.error(request, f'Failed to save credit note: {str(e)}')
            return redirect(self.success_url)
    

    def create_new_entries(self, request, series, date, head1, narration1, credit1, head2, narration2, debit2):
        voucher_config = VoucherConfiguration.objects.filter(series=series, category='Credit Note').first()
    
        if not voucher_config:
            messages.error(request, 'Invalid series for Credit Note.')
            return redirect(self.success_url)
    
        current_serial_no = voucher_config.serial_no
        next_serial_no = current_serial_no + 1
    
        voucher_config.serial_no = next_serial_no
        voucher_config.save()
    
        coid_entry = Table_companyDetailschild.objects.first()
        fycode_entry = Table_companyDetailschild.objects.first()
        coid = coid_entry.company_id if coid_entry else 'C'
        fycode = fycode_entry.fycode if fycode_entry else 'NON'
        user = request.user
    
        Table_DrCrNote.objects.create(
            series=series,
            ndate=date,
            noteno=current_serial_no,
            accountcode=head1,
            narration=narration1,
            dramount=debit2,
            cramount='0',
            ntype='C',
            userid=user.username,  # Correct field name
            coid=coid,
            fycode=fycode,
            brid='1'
        )
    
        Table_DrCrNote.objects.create(
            series=series,
            ndate=date,
            noteno=current_serial_no,
            accountcode=head2,
            narration=narration2,
            dramount='0',
            cramount=credit1,
            ntype='C',
            userid=user.username,  # Correct field name
            coid=coid,
            fycode=fycode,
            brid='1'
        )
    
        self.update_account_balance(head1, -credit1)
        self.update_account_balance(head2, debit2)
    
        messages.success(request, 'Credit note created successfully.')
    

    def update_account_balance(self, account_code, amount):
        accounts = Table_Accountsmaster.objects.filter(account_code=account_code)
    
        if accounts.exists():
            for account in accounts:
                current_balance = float(account.currentbalance or 0)
                account.currentbalance = current_balance + amount
                account.save()
        else:
            raise ValueError(f"No accounts found with account code: {account_code}")













class AccountCreditTableView(ListView):
    model = Table_DrCrNote
    template_name = 'web/accounts/credit-note/credit-table.html'
    context_object_name = "drcrnotesss"

    def get_queryset(self):
        return super().get_queryset().filter(ntype='C')  # Only show Debit notes in the table
    

class SearchCreditTableView(LoginRequiredMixin, TemplateView):
    template_name = 'web/accounts/credit-note/credit-search-box.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['series_options'] = VoucherConfiguration.objects.filter(category='Credit Note').values('series')
        return context

    def post(self, request, *args, **kwargs):
        series = request.POST.get('series')
        serial_no = request.POST.get('serial_no')

        if series and serial_no:
            # Check if the serial number exists
            if Table_DrCrNote.objects.filter(series=series, noteno=serial_no, ntype='C').exists():
                return redirect(reverse('web:account_credit_note', kwargs={'series': series, 'serial_no': serial_no}))
            else:
                context = self.get_context_data(**kwargs)
                context['error'] = 'This serial number does not exist.'
                return render(request, self.template_name, context)
        
        context = self.get_context_data(**kwargs)
        context['error'] = 'Please enter both series and serial number.'
        return render(request, self.template_name, context)


class DeleteCreditNoteView(LoginRequiredMixin, DeleteView):
    model = Table_DrCrNote
    success_url = reverse_lazy("web:account_credit_note")

    def get_object(self, queryset=None):
        pk1 = self.kwargs.get('pk1')
        pk2 = self.kwargs.get('pk2')

        # Fetch the object
        obj = Table_DrCrNote.objects.filter(id=pk1, noteno=pk2).first()
        if not obj:
            raise Http404("No Table_DrCrNote matches the given query.")
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Convert dramount and cramount to float before comparison
        dramount = float(self.object.dramount) if self.object.dramount else 0
        cramount = float(self.object.cramount) if self.object.cramount else 0

        # Update the account balance before deleting
        if dramount > 0:
            self.update_account_balance(self.object.accountcode, dramount)
        elif cramount > 0:
            self.update_account_balance(self.object.accountcode, -cramount)

        # Delete the object
        self.object.delete()

        # Optionally, handle the second object if needed
        obj2 = Table_DrCrNote.objects.filter(noteno=self.object.noteno).exclude(id=self.object.id).first()
        if obj2:
            dramount2 = float(obj2.dramount) if obj2.dramount else 0
            cramount1 = float(obj2.cramount) if obj2.cramount else 0
            
            if dramount2 > 0:
                self.update_account_balance(obj2.accountcode, dramount2)
            elif cramount1 > 0:
                self.update_account_balance(obj2.accountcode, -cramount1)
            obj2.delete()

        messages.success(request, "credit note entry deleted successfully.")
        return redirect(success_url)

    def update_account_balance(self, account_code, amount):
        """Updates the current balance of the account(s) in Table_Accountsmaster."""
        accounts = Table_Accountsmaster.objects.filter(account_code=account_code)
    
        if accounts.exists():
            for account in accounts:
                current_balance = float(account.currentbalance or 0)
                account.currentbalance = current_balance + amount
                account.save()
        else:
            raise ValueError(f"No accounts found with account code: {account_code}")
    

# CONTRA ENTRY

from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import VoucherConfiguration, Table_Accountsmaster, Wallet, Table_Contra_Entry, Table_Acntchild, Table_companyDetailschild

from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import VoucherConfiguration, Table_Accountsmaster, Wallet, Table_Contra_Entry, Table_Acntchild, Table_companyDetailschild

class ContraEntryView(View):
    template_name = 'web/accounts/contra-entry/contra_entry.html'

    def get(self, request, *args, **kwargs):
        vouchers = VoucherConfiguration.objects.filter(category='Contra Entry')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Accounts', 'Customers', 'Suppliers'])
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Accounts', 'Customers', 'Suppliers'])
        wallet = Wallet.objects.first()

        next_serial_numbers = {}
        for voucher in vouchers:
            last_serial = Table_Contra_Entry.objects.filter(series=voucher.series).order_by('-voucher_no').first()
            next_serial_numbers[voucher.series] = str(int(last_serial.voucher_no) + 1) if last_serial else voucher.serial_no

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'head_accounts': head_accounts,
            'next_serial_numbers': next_serial_numbers,
            'user_id': request.user.id,
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('series')
            voucher_no = request.POST.get('voucher_no')
            vdate = request.POST.get('vdate')
            user_id = request.user.id
            branch_id = '1'
            heads = request.POST.getlist('head')
            head_codes = request.POST.getlist('head_code')
            narrations = request.POST.getlist('narration[]')
            debit = request.POST.getlist('dramount[]')
            credit = request.POST.getlist('cramount[]')
    
            if not (len(heads) == len(narrations) == len(debit) == len(credit) == len(head_codes)):
                raise ValueError("Mismatched input lengths in form data.")
    
            total_debit = sum(float(d) for d in debit if d)
            total_credit = sum(float(c) for c in credit if c)
    
            company_details = Table_companyDetailschild.objects.first()
            coid = company_details.company_id if company_details else ''
            fycode = company_details.fycode if company_details else ''
    
            with transaction.atomic():
                entries = []
                for head, head_code, narration, debit_amount, credit_amount in zip(heads, head_codes, narrations, debit, credit):
                    entries.append(
                        Table_Contra_Entry(
                            series=series,
                            voucher_no=voucher_no,
                            vdate=vdate,
                            accountcode=head_code,
                            narration=narration,
                            dramount=float(debit_amount) if debit_amount else 0,
                            cramount=float(credit_amount) if credit_amount else 0,
                            user_id=user_id,
                            fycode=fycode,
                            coid=coid,
                            brid=branch_id
                        )
                    )
                Table_Contra_Entry.objects.bulk_create(entries)
    
                account_updates = {}
                for head_code, debit_amount, credit_amount in zip(head_codes, debit, credit):
                    if debit_amount:
                        if head_code not in account_updates:
                            account_updates[head_code] = 0
                        account_updates[head_code] += float(debit_amount)
                    if credit_amount:
                        if head_code not in account_updates:
                            account_updates[head_code] = 0
                        account_updates[head_code] -= float(credit_amount)
                
                accounts_to_update = []
                for head_code, amount in account_updates.items():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=head_code)
                        account.currentbalance = (float(account.currentbalance or 0) + amount)
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        pass
                Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])
    
                voucher_configs = VoucherConfiguration.objects.filter(series=series, category='Contra Entry')
                for voucher_config in voucher_configs:
                    voucher_config.serial_no = voucher_no
                    voucher_config.save()
    
            messages.success(request, "Contra saved successfully!")
            return redirect('web:account_contra_entry')
        except Exception as e:
            print("Error saving contra entry: ", e)
            messages.error(request, f"Error saving contra entry: {str(e)}")
            return self.get(request)
    


    




class ContraEntryTable(LoginRequiredMixin, ListView):
    model = Table_Contra_Entry
    template_name = 'web/accounts/contra-entry/contra-entry-table.html'
    context_object_name = "contraentrys"


class SearchContraEntryView(LoginRequiredMixin, View):
    template_name = 'web/accounts/contra-entry/search-contra-entry.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series', '')
        voucher_no = request.GET.get('VoucherNo', '')

        error_message = None
        if not series or not voucher_no:
            error_message = "Please provide both series and voucher number."

        vouchers = VoucherConfiguration.objects.filter(category='Contra Entry')
        return render(request, self.template_name, {'vouchers': vouchers, 'error_message': error_message})


from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal

class EditContraEntry(LoginRequiredMixin, View):
    template_name = 'web/accounts/contra-entry/edit-contra-entry.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series')
        voucher_no = request.GET.get('VoucherNo')

        vouchers = VoucherConfiguration.objects.filter(category='Contra Entry')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Accounts', 'Customers', 'Suppliers'])
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Accounts', 'Customers', 'Suppliers'])
        table_acntchildren = Table_Acntchild.objects.filter(account_master__category__in=['Accounts', 'Customers', 'Suppliers'])

        voucher_entries = Table_Contra_Entry.objects.filter(series=series, voucher_no=voucher_no)

        if not voucher_entries:
            return redirect('web:search_contra_entry')

        valid_account_codes = head_accounts.values_list('account_code', flat=True)

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'head_accounts': head_accounts,
            'table_acntchildren': table_acntchildren,
            'voucher_entries': voucher_entries,
            'user_id': request.user.id,
            'valid_account_codes': valid_account_codes
        })


    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('series')
            vdate = request.POST.get('vdate')
            voucher_no = request.POST.get('voucher_no')
            if not voucher_no:
                raise ValueError("Voucher number is required.")
            user_id = request.user.id

            company_details = Table_companyDetailschild.objects.first()
            if not company_details:
                raise ValueError("Company details not found.")

            fycode = company_details.fycode
            coid = company_details.company_id
            branch_id = '1'

            heads = request.POST.getlist('head')
            narrations = request.POST.getlist('narration[]')
            debit = request.POST.getlist('dramount[]')
            credit = request.POST.getlist('cramount[]')

            if not (len(heads) == len(narrations) == len(debit) == len(credit)):
                raise ValueError("Mismatched input lengths in form data.")

            # Convert to Decimal for consistency
            debit = [Decimal(d) if d else Decimal('0') for d in debit]
            credit = [Decimal(c) if c else Decimal('0') for c in credit]

            total_debit = sum(debit)
            total_credit = sum(credit)

            voucher_config = VoucherConfiguration.objects.get(series=series, category='Contra Entry')

            with transaction.atomic():
                # Fetch existing entries and compute old debit and credit totals
                existing_entries = Table_Contra_Entry.objects.filter(series=series, voucher_no=voucher_no)
                old_account_updates = {}
                for entry in existing_entries:
                    if entry.accountcode not in old_account_updates:
                        old_account_updates[entry.accountcode] = Decimal('0')
                    old_account_updates[entry.accountcode] += (Decimal(entry.dramount) - Decimal(entry.cramount))

                # Delete existing entries
                existing_entries.delete()

                # Create new entries
                for head, narration, debit_amount, credit_amount in zip(heads, narrations, debit, credit):
                    Table_Contra_Entry.objects.create(
                        series=series,
                        voucher_no=voucher_no,
                        vdate=vdate,
                        accountcode=head,
                        narration=narration,
                        dramount=debit_amount,
                        cramount=credit_amount,
                        user_id=user_id,
                        fycode=fycode,
                        coid=coid,
                        brid=branch_id
                    )

                # Compute new debit and credit totals
                new_account_updates = {}
                for head, debit_amount, credit_amount in zip(heads, debit, credit):
                    if debit_amount:
                        if head not in new_account_updates:
                            new_account_updates[head] = Decimal('0')
                        new_account_updates[head] += debit_amount
                    if credit_amount:
                        if head not in new_account_updates:
                            new_account_updates[head] = Decimal('0')
                        new_account_updates[head] -= credit_amount

                # Update account balances
                accounts_to_update = []
                for head_code, new_amount in new_account_updates.items():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=head_code)
                        # Adjust the balance by subtracting old amounts and adding new amounts
                        old_amount = old_account_updates.get(head_code, Decimal('0'))
                        account.currentbalance = (Decimal(account.currentbalance or '0') - old_amount + new_amount)
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account with code {head_code} does not exist. Skipping update.")

                Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])

                # Update the voucher configuration with the new serial number if needed
                voucher_no_int = int(voucher_no)
                if voucher_no_int > voucher_config.serial_no:
                    voucher_config.serial_no = voucher_no_int
                    voucher_config.save()

            messages.success(request, "Contra updated successfully!")
            return redirect('web:account_contra_entry')
        except Exception as e:
            print("Error saving contra entry: ", e)
            messages.error(request, f"Error saving contra entry: {str(e)}")
            return self.get(request, error=str(e))





from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal

class DeleteContraEntryView(LoginRequiredMixin, View):
    def delete(self, request, voucher_no, *args, **kwargs):
        try:
            with transaction.atomic():
                # Retrieve contra entries to delete
                contra_entries = Table_Contra_Entry.objects.filter(voucher_no=voucher_no)
                
                if not contra_entries.exists():
                    return JsonResponse({'success': False, 'message': 'No entries found.'})
                
                # Prepare to accumulate amounts to adjust account balances
                account_updates = {}
                for entry in contra_entries:
                    head_code = entry.accountcode
                    dr_amount = Decimal(entry.dramount) if entry.dramount else Decimal('0')
                    cr_amount = Decimal(entry.cramount) if entry.cramount else Decimal('0')
                    
                    if head_code not in account_updates:
                        account_updates[head_code] = Decimal('0')
                    # Subtract the debit amount and add the credit amount
                    account_updates[head_code] -= dr_amount
                    account_updates[head_code] += cr_amount
                
                # Delete the contra entries
                contra_entries.delete()

                # Update the current balance for affected accounts
                accounts_to_update = []
                for head_code, amount_change in account_updates.items():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=head_code)
                        account.currentbalance = Decimal(account.currentbalance or '0') + amount_change
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account with code {head_code} does not exist. Skipping update.")
                
                if accounts_to_update:
                    Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])

                return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error deleting contra entry: {e}")
            return JsonResponse({'success': False, 'message': str(e)})



# - Journal Entry

from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Table_Journal_Entry, Table_Accountsmaster, VoucherConfiguration, Table_companyDetailschild
from decimal import Decimal

class JournalEntryView(View):
    template_name = 'web/accounts/journal-entry/journal-entry.html'

    def get(self, request, *args, **kwargs):
        vouchers = VoucherConfiguration.objects.filter(category='Journal Entry')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Bank', 'Cashbook'])
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Bank', 'Cashbook'])

        next_serial_numbers = {}
        for voucher in vouchers:
            last_serial = Table_Journal_Entry.objects.filter(series=voucher.series).order_by('-voucher_no').first()
            next_serial_numbers[voucher.series] = str(int(last_serial.voucher_no) + 1) if last_serial else voucher.serial_no

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'head_accounts': head_accounts,
            'next_serial_numbers': next_serial_numbers,
            'user_id': request.user.id,
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('series')
            voucher_no = request.POST.get('voucher_no')
            vdate = request.POST.get('vdate')
            user_id = request.user.id
            branch_id = '1'
            heads = request.POST.getlist('head')
            head_codes = request.POST.getlist('head_code')
            narrations = request.POST.getlist('narration[]')
            debit = request.POST.getlist('dramount[]')
            credit = request.POST.getlist('cramount[]')

            if not (len(heads) == len(narrations) == len(debit) == len(credit) == len(head_codes)):
                raise ValueError("Mismatched input lengths in form data.")

            total_amount = sum(float(amount) for amount in debit if amount)

            company_details = Table_companyDetailschild.objects.first()
            coid = company_details.company_id if company_details else ''
            fycode = company_details.fycode if company_details else ''

            with transaction.atomic():
                # Fetch existing entries and compute old debit and credit totals
                existing_entries = Table_Journal_Entry.objects.filter(series=series, voucher_no=voucher_no)
                old_account_updates = {}
                for entry in existing_entries:
                    if entry.accountcode not in old_account_updates:
                        old_account_updates[entry.accountcode] = Decimal('0')
                    old_account_updates[entry.accountcode] += (Decimal(entry.dramount) - Decimal(entry.cramount))

                # Delete existing entries
                existing_entries.delete()

                # Create new entries
                for head, head_code, narration, debit_amount, credit_amount in zip(heads, head_codes, narrations, debit, credit):
                    if not head_code or not head_code.isdigit():  # Skip if head_code is empty or not a number
                        continue

                    Table_Journal_Entry.objects.create(
                        series=series,
                        voucher_no=voucher_no,
                        vdate=vdate,
                        accountcode=head_code,
                        narration=narration,
                        dramount=float(debit_amount) if debit_amount else 0,
                        cramount=float(credit_amount) if credit_amount else 0,
                        user_id=user_id,
                        fycode=fycode,
                        coid=coid,
                        brid=branch_id
                    )

                # Compute new debit and credit totals
                new_account_updates = {}
                for head, head_code, debit_amount, credit_amount in zip(heads, head_codes, debit, credit):
                    if not head_code or not head_code.isdigit():  # Skip if head_code is empty or not a number
                        continue

                    if debit_amount:
                        if head_code not in new_account_updates:
                            new_account_updates[head_code] = Decimal('0')
                        new_account_updates[head_code] += Decimal(debit_amount)
                    if credit_amount:
                        if head_code not in new_account_updates:
                            new_account_updates[head_code] = Decimal('0')
                        new_account_updates[head_code] -= Decimal(credit_amount)

                # Update account balances
                accounts_to_update = []
                for head_code, new_amount in new_account_updates.items():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=head_code)
                        old_amount = old_account_updates.get(head_code, Decimal('0'))
                        account.currentbalance = (Decimal(account.currentbalance or '0') - old_amount + new_amount)
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account with code {head_code} does not exist. Skipping update.")

                Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])

                # Update the voucher configuration with the new serial number if needed
                voucher_no_int = int(voucher_no)
                voucher_config = VoucherConfiguration.objects.get(series=series, category='Journal Entry')
                if voucher_no_int > voucher_config.serial_no:
                    voucher_config.serial_no = voucher_no_int
                    voucher_config.save()

            messages.success(request, "Journal saved successfully!")
            return redirect('web:account_journal_entry')
        except Exception as e:
            print("Error saving Journal Entry: ", e)
            messages.error(request, f"Error saving Journal Entry: {str(e)}")
            return self.get(request)




class JournalEntryTable(LoginRequiredMixin, ListView):
    model = Table_Journal_Entry
    template_name = 'web/accounts/journal-entry/journal-entry-table.html'
    context_object_name = "journalentrys"


class SearchJournalEntryView(LoginRequiredMixin, View):
    template_name = 'web/accounts/journal-entry/search-journal-entry.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series', '')
        voucher_no = request.GET.get('VoucherNo', '')

        error_message = None
        if not series or not voucher_no:
            error_message = "Please provide both series and voucher number."

        vouchers = VoucherConfiguration.objects.filter(category='Journal Entry')
        return render(request, self.template_name, {'vouchers': vouchers, 'error_message': error_message})


class EditJournalEntry(LoginRequiredMixin, View):
    template_name = 'web/accounts/journal-entry/edit-journal-entry.html'

    def get(self, request, *args, **kwargs):
        series = request.GET.get('Series')
        voucher_no = request.GET.get('VoucherNo')

        vouchers = VoucherConfiguration.objects.filter(category='Journal Entry')
        accountmas = Table_Accountsmaster.objects.filter(category__in=['Bank', 'Cashbook'])
        wallet = Wallet.objects.first()
        head_accounts = Table_Accountsmaster.objects.exclude(category__in=['Bank', 'Cashbook'])
        table_acntchildren = Table_Acntchild.objects.select_related('account_master').filter(
            account_master__category__in=['Bank', 'Cashbook']
        )

        voucher_entries = Table_Journal_Entry.objects.filter(series=series, voucher_no=voucher_no)

        if not voucher_entries:
            return redirect('web:search_journal_entry')  # Ensure this matches the name in urls.py

        valid_account_codes = head_accounts.values_list('account_code', flat=True)

        return render(request, self.template_name, {
            'vouchers': vouchers,
            'accountmas': accountmas,
            'wallet': wallet,
            'head_accounts': head_accounts,
            'table_acntchildren': table_acntchildren,
            'voucher_entries': voucher_entries,
            'user_id': request.user.id,
            'valid_account_codes': valid_account_codes
        })

    def post(self, request, *args, **kwargs):
        try:
            series = request.POST.get('series')
            vdate = request.POST.get('vdate')
            voucher_no = request.POST.get('voucher_no')
            if not voucher_no:
                raise ValueError("Voucher number is required.")
            user_id = request.user.id

            company_details = Table_companyDetailschild.objects.first()
            if not company_details:
                raise ValueError("Company details not found.")

            fycode = company_details.fycode
            coid = company_details.company_id  # Assuming `company_id` is the ID for coid
            branch_id = '1'  # Adjust as needed

            heads = request.POST.getlist('head')
            narrations = request.POST.getlist('narration[]')
            debit = request.POST.getlist('dramount[]')
            credit = request.POST.getlist('cramount[]')

            if not (len(heads) == len(narrations) == len(debit) == len(credit)):
                raise ValueError("Mismatched input lengths in form data.")

            # Convert to Decimal for consistency
            debit = [Decimal(d) if d else Decimal('0') for d in debit]
            credit = [Decimal(c) if c else Decimal('0') for c in credit]

            total_amount = sum(debit)

            voucher_config = VoucherConfiguration.objects.get(series=series, category='Journal Entry')

            with transaction.atomic():
                # Fetch existing entries and compute old debit and credit totals
                existing_entries = Table_Journal_Entry.objects.filter(series=series, voucher_no=voucher_no)
                old_account_updates = {}
                for entry in existing_entries:
                    if entry.accountcode not in old_account_updates:
                        old_account_updates[entry.accountcode] = Decimal('0')
                    old_account_updates[entry.accountcode] += (Decimal(entry.dramount) - Decimal(entry.cramount))

                # Delete existing entries
                existing_entries.delete()

                # Create new entries
                for head, narration, debit_amount, credit_amount in zip(heads, narrations, debit, credit):
                    Table_Journal_Entry.objects.create(
                        series=series,
                        voucher_no=voucher_no,
                        vdate=vdate,
                        accountcode=head,
                        narration=narration,
                        dramount=debit_amount,
                        cramount=credit_amount,
                        user_id=user_id,
                        fycode=fycode,
                        coid=coid,
                        brid=branch_id
                    )

                # Compute new debit and credit totals
                new_account_updates = {}
                for head, debit_amount, credit_amount in zip(heads, debit, credit):
                    if debit_amount:
                        if head not in new_account_updates:
                            new_account_updates[head] = Decimal('0')
                        new_account_updates[head] += debit_amount
                    if credit_amount:
                        if head not in new_account_updates:
                            new_account_updates[head] = Decimal('0')
                        new_account_updates[head] -= credit_amount

                # Update account balances
                accounts_to_update = []
                for head_code, new_amount in new_account_updates.items():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=head_code)
                        old_amount = old_account_updates.get(head_code, Decimal('0'))
                        account.currentbalance = (Decimal(account.currentbalance or '0') - old_amount + new_amount)
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account with code {head_code} does not exist. Skipping update.")

                Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])

                # Update the voucher configuration with the new serial number if needed
                voucher_no_int = int(voucher_no)
                if voucher_no_int > voucher_config.serial_no:
                    voucher_config.serial_no = voucher_no_int
                    voucher_config.save()

            messages.success(request, "Journal entry updated successfully!")
            return redirect('web:account_journal_entry')
        except Exception as e:
            print("Error updating Journal Entry: ", e)
            messages.error(request, f"Error updating Journal Entry: {str(e)}")
            return self.get(request)



class DeleteJournalEntryView(LoginRequiredMixin, View):
    def delete(self, request, voucher_no, *args, **kwargs):
        try:
            # Fetch the journal entries to be deleted
            entries = Table_Journal_Entry.objects.filter(voucher_no=voucher_no)
            
            if entries.exists():
                # Compute the totals to be removed
                debit_totals = {}
                credit_totals = {}
                
                for entry in entries:
                    account_code = entry.accountcode
                    debit_amount = Decimal(entry.dramount)
                    credit_amount = Decimal(entry.cramount)
                    
                    if account_code not in debit_totals:
                        debit_totals[account_code] = Decimal('0')
                        credit_totals[account_code] = Decimal('0')
                    
                    debit_totals[account_code] += debit_amount
                    credit_totals[account_code] += credit_amount

                # Delete the entries
                entries.delete()

                # Update the balances
                accounts_to_update = []
                for account_code in debit_totals.keys():
                    try:
                        account = Table_Accountsmaster.objects.get(account_code=account_code)
                        old_balance = Decimal(account.currentbalance or '0')
                        debit_total = debit_totals.get(account_code, Decimal('0'))
                        credit_total = credit_totals.get(account_code, Decimal('0'))
                        new_balance = old_balance - debit_total + credit_total
                        account.currentbalance = new_balance
                        accounts_to_update.append(account)
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Account with code {account_code} does not exist. Skipping update.")

                Table_Accountsmaster.objects.bulk_update(accounts_to_update, ['currentbalance'])

                return JsonResponse({'success': True})
            return JsonResponse({'success': False})
        except Exception as e:
            print("Error deleting Journal Entry: ", e)
            return JsonResponse({'success': False, 'error': str(e)})

    
# ############################################# ACCOUNT ####################################################



from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

class LedgerSearchView(LoginRequiredMixin, TemplateView):
    template_name = "web/accounts/ledger/ledger_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch the first (or specific) company details record for finyearfrom
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context["finyearfrom"] = company_details.finyearfrom
        context["head_accounts"] = Table_Accountsmaster.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        account_code = request.POST.get("Accountcode")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        
        if not account_code:
            messages.error(request, "No account head selected. Please select an account head.")
            return self.get(request, *args, **kwargs)  # Return to the form page with error message

        # If everything is valid, redirect to the ledger page
        return HttpResponseRedirect(
            reverse(
                "web:ledger",
                kwargs={
                    "account_code": account_code,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
        )



from django.utils.dateparse import parse_date
from decimal import Decimal
from .models import Table_Voucher, Table_DrCrNote, Table_Accountsmaster
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from decimal import Decimal
from datetime import datetime

class LedgerView(LoginRequiredMixin, View):
    def get(self, request, account_code, start_date, end_date):
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        # Fetch account details
        account_master = Table_Accountsmaster.objects.get(account_code=account_code)
        
        # Fetch company details
        company_details = Table_Companydetailsmaster.objects.first()  # Assuming there's only one record

        # Convert initial balance to Decimal if it is not already
        opbalance = Decimal(account_master.opbalance)

        # Calculate the last closing balance before start_date
        def get_last_closing_balance():
            entries = (
                list(Table_Voucher.objects.filter(Accountcode=account_code, Vdate__lt=start_date)) +
                list(Table_DrCrNote.objects.filter(accountcode=account_code, ndate__lt=start_date)) +
                list(Table_Journal_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date)) +
                list(Table_Contra_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date))
            )
            # Sort by date (Vdate for voucher, ndate for DR/CR, vdate for journal/contra)
            entries.sort(key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or getattr(x, 'vdate', None)
            ))

            last_closing_balance = opbalance
            for entry in entries:
                if hasattr(entry, "Vdate"):
                    if entry.CStatus == "P":
                        last_closing_balance += Decimal(entry.VAmount or "0.00")
                    elif entry.CStatus == "R":
                        last_closing_balance -= Decimal(entry.VAmount or "0.00")
                elif hasattr(entry, "ndate"):
                    if entry.ntype == 'C':
                        last_closing_balance += Decimal(entry.cramount or "0.00")
                        last_closing_balance -= Decimal(entry.dramount or "0.00")
                    else:
                        last_closing_balance += Decimal(entry.dramount or "0.00")
                        last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Journal_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Contra_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")

            return last_closing_balance

        opening_balance = get_last_closing_balance()

        # Fetch entries within date range
        voucher_entries = Table_Voucher.objects.filter(
            Accountcode=account_code, Vdate__range=[start_date, end_date]
        )

        drcr_entries = Table_DrCrNote.objects.filter(
            accountcode=account_code, ndate__range=[start_date, end_date]
        )

        journal_entries = Table_Journal_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        )

        contra_entries = Table_Contra_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        )

        # Combine and sort entries by date
        combined_entries = sorted(
            list(voucher_entries) +
            list(drcr_entries) +
            list(journal_entries) +
            list(contra_entries),
            key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or getattr(x, 'vdate', None)
            )
        )

        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        closing_balance = opening_balance  # Start with the opening balance

        entry_list = []

        for entry in combined_entries:
            entry_dict = {}

            if hasattr(entry, "Vdate"):  # Table_Voucher entry
                debit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "P"
                    else Decimal("0.00")
                )
                credit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "R"
                    else Decimal("0.00")
                )
                entry_dict = {
                    "date": entry.Vdate,
                    "voucher_number": entry.VoucherNo or entry.Series,
                    "narration": entry.Narration,
                    "status": entry.CStatus,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif hasattr(entry, "ndate"):  # Table_DrCrNote entry
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                if entry.ntype == 'C':  # Assuming 'C' stands for Credit Note
                    debit_amount, credit_amount = credit_amount, debit_amount
                entry_dict = {
                    "date": entry.ndate,
                    "voucher_number": entry.noteno or entry.series,
                    "narration": entry.narration,
                    "type": entry.ntype,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Journal_Entry):  # Table_Journal_Entry
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "is_journal_entry": True,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Contra_Entry):  # Table_Contra_Entry
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "is_journal_entry": False,
                    "is_contra_entry": True,
                }

            # Update the running balance
            closing_balance += entry_dict.get("debit", Decimal("0.00"))
            closing_balance -= entry_dict.get("credit", Decimal("0.00"))

            # Add closing balance to the entry dictionary
            entry_dict["closing_balance"] = closing_balance

            total_debit += entry_dict.get("debit", Decimal("0.00"))
            total_credit += entry_dict.get("credit", Decimal("0.00"))

            entry_list.append(entry_dict)

        balance_cd = closing_balance  # Final closing balance

        # Determine debit and credit values for the opening balance row
        opening_balance_debit = max(opening_balance, Decimal("0.00"))
        opening_balance_credit = -min(opening_balance, Decimal("0.00"))

        context = {
            "account_master": account_master,
            "entries": entry_list,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance_cd": balance_cd,
            "opening_balance": opening_balance,  # Added opening balance to context
            "opening_balance_debit": opening_balance_debit,
            "opening_balance_credit": opening_balance_credit,
            "start_date": start_date,
            "end_date": end_date,
            "company_name": company_details.companyname,
            "company_phone": company_details.phoneno,
            "company_address": company_details.address1,
            "company_gst": company_details.gst,
        }

        return render(request, "web/accounts/ledger/ledger.html", context)






class CashBookSearchView(LoginRequiredMixin, TemplateView):
    template_name = "web/accounts/cash-book/cashbook_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch the first (or specific) company details record for finyearfrom
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context["finyearfrom"] = company_details.finyearfrom

        # Filter head accounts with category 'Cashbook'
        context["head_accounts"] = Table_Accountsmaster.objects.filter(category='Cashbook')
        return context

    def post(self, request, *args, **kwargs):
        account_code = request.POST.get("Accountcode")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        
        if not account_code:
            messages.error(request, "No account head selected. Please select an account head.")
            return self.get(request, *args, **kwargs)  # Return to the form page with error message

        # If everything is valid, redirect to the ledger page
        return HttpResponseRedirect(
            reverse(
                "web:cashbook",
                kwargs={
                    "account_code": account_code,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
        )




class CashBookView(LoginRequiredMixin, View):
    def get(self, request, account_code, start_date, end_date):
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        # Fetch account details
        account_master = Table_Accountsmaster.objects.get(account_code=account_code)
        
        # Fetch company details
        company_details = Table_Companydetailsmaster.objects.first()  # Assuming there's only one record

        # Convert initial balance to Decimal if it is not already
        opbalance = Decimal(account_master.opbalance)

        # Calculate the last closing balance before the start_date
        def get_last_closing_balance():
            entries = (
                list(Table_Voucher.objects.filter(Accountcode=account_code, Vdate__lt=start_date)) +
                list(Table_DrCrNote.objects.filter(accountcode=account_code, ndate__lt=start_date)) +
                list(Table_Journal_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date)) +
                list(Table_Contra_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date))
            )
            entries.sort(key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or datetime.min.date()
            ))
            
            last_closing_balance = opbalance
            for entry in entries:
                if hasattr(entry, "Vdate"):
                    if entry.CStatus == "P":
                        last_closing_balance += Decimal(entry.VAmount or "0.00")
                    elif entry.CStatus == "R":
                        last_closing_balance -= Decimal(entry.VAmount or "0.00")
                elif hasattr(entry, "ndate"):
                    if entry.ntype == 'C':
                        last_closing_balance += Decimal(entry.cramount or "0.00")
                        last_closing_balance -= Decimal(entry.dramount or "0.00")
                    else:
                        last_closing_balance += Decimal(entry.dramount or "0.00")
                        last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Journal_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Contra_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")

            return last_closing_balance

        opening_balance = get_last_closing_balance()

        # Fetch entries from Table_Voucher, Table_DrCrNote, Table_Journal_Entry, and Table_Contra_Entry within date range
        voucher_entries = Table_Voucher.objects.filter(
            Accountcode=account_code, Vdate__range=[start_date, end_date]
        ).order_by("Vdate")

        drcr_entries = Table_DrCrNote.objects.filter(
            accountcode=account_code, ndate__range=[start_date, end_date]
        ).order_by("ndate")

        journal_entries = Table_Journal_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        ).order_by("vdate")

        contra_entries = Table_Contra_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        ).order_by("vdate")

        # Combine and sort entries, using a default date (e.g., datetime.min.date()) if the date is None
        combined_entries = (
            list(voucher_entries) +
            list(drcr_entries) +
            list(journal_entries) +
            list(contra_entries)
        )
        combined_entries.sort(
            key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or datetime.min.date()
            )
        )

        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        closing_balance = opening_balance  # Start with the opening balance

        entry_list = []

        for entry in combined_entries:
            entry_dict = {}
            head = ""
            
            if hasattr(entry, "Vdate"):  # Table_Voucher entry
                head = Table_Accountsmaster.objects.get(account_code=entry.Accountcode).head
                debit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "P"
                    else Decimal("0.00")
                )
                credit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "R"
                    else Decimal("0.00")
                )
                entry_dict = {
                    "date": entry.Vdate,
                    "voucher_number": entry.VoucherNo or entry.Series,
                    "narration": entry.Narration,
                    "status": entry.CStatus,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif hasattr(entry, "ndate"):  # Table_DrCrNote entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                if entry.ntype == 'C':  # Assuming 'C' stands for Credit Note
                    debit_amount, credit_amount = credit_amount, debit_amount
                entry_dict = {
                    "date": entry.ndate,
                    "voucher_number": entry.noteno or entry.series,
                    "narration": entry.narration,
                    "type": entry.ntype,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Journal_Entry):  # Table_Journal_Entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": True,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Contra_Entry):  # Table_Contra_Entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": True,
                }

            # Update the running balance
            closing_balance += entry_dict.get("debit", Decimal("0.00"))
            closing_balance -= entry_dict.get("credit", Decimal("0.00"))

            # Add closing balance to the entry dictionary
            entry_dict["closing_balance"] = closing_balance

            total_debit += entry_dict.get("debit", Decimal("0.00"))
            total_credit += entry_dict.get("credit", Decimal("0.00"))

            entry_list.append(entry_dict)

        balance_cd = closing_balance  # Final closing balance

        # Determine debit and credit values for the opening balance row
        opening_balance_debit = max(opening_balance, Decimal("0.00"))
        opening_balance_credit = -min(opening_balance, Decimal("0.00"))

        context = {
            "account_master": account_master,
            "entries": entry_list,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance_cd": balance_cd,
            "opening_balance": opening_balance,  # Added opening balance to context
            "opening_balance_debit": opening_balance_debit,
            "opening_balance_credit": opening_balance_credit,
            "start_date": start_date,
            "end_date": end_date,
            "company_name": company_details.companyname,
            "company_phone": company_details.phoneno,
            "company_address": company_details.address1,
            "company_gst": company_details.gst,
        }

        return render(request, "web/accounts/cash-book/cashbook.html", context)








class BankBookSearchView(LoginRequiredMixin, TemplateView):
    template_name = "web/accounts/bank-book/bankbook_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch the first (or specific) company details record for finyearfrom
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context["finyearfrom"] = company_details.finyearfrom

        # Filter head accounts with category 'Cashbook'
        context["head_accounts"] = Table_Accountsmaster.objects.filter(category='Bank')
        return context

    def post(self, request, *args, **kwargs):
        account_code = request.POST.get("Accountcode")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        
        if not account_code:
            messages.error(request, "No account head selected. Please select an account head.")
            return self.get(request, *args, **kwargs)  # Return to the form page with error message

        # If everything is valid, redirect to the ledger page
        return HttpResponseRedirect(
            reverse(
                "web:bankbook",
                kwargs={
                    "account_code": account_code,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
        )


class BankBookView(LoginRequiredMixin, View):
    def get(self, request, account_code, start_date, end_date):
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        # Fetch account details
        account_master = Table_Accountsmaster.objects.get(account_code=account_code)
        
        # Fetch company details
        company_details = Table_Companydetailsmaster.objects.first()  # Assuming there's only one record

        # Convert initial balance to Decimal if it is not already
        opbalance = Decimal(account_master.opbalance)

        # Calculate the last closing balance before the start_date
        def get_last_closing_balance():
            entries = (
                list(Table_Voucher.objects.filter(Accountcode=account_code, Vdate__lt=start_date)) +
                list(Table_DrCrNote.objects.filter(accountcode=account_code, ndate__lt=start_date)) +
                list(Table_Journal_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date)) +
                list(Table_Contra_Entry.objects.filter(accountcode=account_code, vdate__lt=start_date))
            )
            entries.sort(key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or datetime.min.date()
            ))
            
            last_closing_balance = opbalance
            for entry in entries:
                if hasattr(entry, "Vdate"):
                    if entry.CStatus == "P":
                        last_closing_balance += Decimal(entry.VAmount or "0.00")
                    elif entry.CStatus == "R":
                        last_closing_balance -= Decimal(entry.VAmount or "0.00")
                elif hasattr(entry, "ndate"):
                    if entry.ntype == 'C':
                        last_closing_balance += Decimal(entry.cramount or "0.00")
                        last_closing_balance -= Decimal(entry.dramount or "0.00")
                    else:
                        last_closing_balance += Decimal(entry.dramount or "0.00")
                        last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Journal_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")
                elif isinstance(entry, Table_Contra_Entry):
                    last_closing_balance += Decimal(entry.dramount or "0.00")
                    last_closing_balance -= Decimal(entry.cramount or "0.00")

            return last_closing_balance

        opening_balance = get_last_closing_balance()

        # Fetch entries from Table_Voucher, Table_DrCrNote, Table_Journal_Entry, and Table_Contra_Entry within date range
        voucher_entries = Table_Voucher.objects.filter(
            Accountcode=account_code, Vdate__range=[start_date, end_date]
        ).order_by("Vdate")

        drcr_entries = Table_DrCrNote.objects.filter(
            accountcode=account_code, ndate__range=[start_date, end_date]
        ).order_by("ndate")

        journal_entries = Table_Journal_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        ).order_by("vdate")

        contra_entries = Table_Contra_Entry.objects.filter(
            accountcode=account_code, vdate__range=[start_date, end_date]
        ).order_by("vdate")

        # Combine and sort entries, using a default date (e.g., datetime.min.date()) if the date is None
        combined_entries = (
            list(voucher_entries) +
            list(drcr_entries) +
            list(journal_entries) +
            list(contra_entries)
        )
        combined_entries.sort(
            key=lambda x: (
                getattr(x, 'Vdate', None) or getattr(x, 'ndate', None) or datetime.min.date()
            )
        )

        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        closing_balance = opening_balance  # Start with the opening balance

        entry_list = []

        for entry in combined_entries:
            entry_dict = {}
            head = ""
            
            if hasattr(entry, "Vdate"):  # Table_Voucher entry
                head = Table_Accountsmaster.objects.get(account_code=entry.Accountcode).head
                debit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "P"
                    else Decimal("0.00")
                )
                credit_amount = (
                    Decimal(entry.VAmount or "0.00")
                    if entry.CStatus == "R"
                    else Decimal("0.00")
                )
                entry_dict = {
                    "date": entry.Vdate,
                    "voucher_number": entry.VoucherNo or entry.Series,
                    "narration": entry.Narration,
                    "status": entry.CStatus,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif hasattr(entry, "ndate"):  # Table_DrCrNote entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                if entry.ntype == 'C':  # Assuming 'C' stands for Credit Note
                    debit_amount, credit_amount = credit_amount, debit_amount
                entry_dict = {
                    "date": entry.ndate,
                    "voucher_number": entry.noteno or entry.series,
                    "narration": entry.narration,
                    "type": entry.ntype,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Journal_Entry):  # Table_Journal_Entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": True,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Contra_Entry):  # Table_Contra_Entry
                head = Table_Accountsmaster.objects.get(account_code=entry.accountcode).head
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                entry_dict = {
                    "date": entry.vdate,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "head": head,
                    "is_journal_entry": False,
                    "is_contra_entry": True,
                }

            # Update the running balance
            closing_balance += entry_dict.get("debit", Decimal("0.00"))
            closing_balance -= entry_dict.get("credit", Decimal("0.00"))

            # Add closing balance to the entry dictionary
            entry_dict["closing_balance"] = closing_balance

            total_debit += entry_dict.get("debit", Decimal("0.00"))
            total_credit += entry_dict.get("credit", Decimal("0.00"))

            entry_list.append(entry_dict)

        balance_cd = closing_balance  # Final closing balance

        # Determine debit and credit values for the opening balance row
        opening_balance_debit = max(opening_balance, Decimal("0.00"))
        opening_balance_credit = -min(opening_balance, Decimal("0.00"))

        context = {
            "account_master": account_master,
            "entries": entry_list,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance_cd": balance_cd,
            "opening_balance": opening_balance,  # Added opening balance to context
            "opening_balance_debit": opening_balance_debit,
            "opening_balance_credit": opening_balance_credit,
            "start_date": start_date,
            "end_date": end_date,
            "company_name": company_details.companyname,
            "company_phone": company_details.phoneno,
            "company_address": company_details.address1,
            "company_gst": company_details.gst,
        }

        return render(request, "web/accounts/bank-book/bankbook.html", context)


from datetime import datetime



class DayBookSearchView(LoginRequiredMixin, TemplateView):
    template_name = "web/accounts/day-book/daybook_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_details = Table_Companydetailsmaster.objects.first()
        if company_details:
            context["finyearfrom"] = company_details.finyearfrom
        return context

    def post(self, request, *args, **kwargs):
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            messages.error(request, "Please select both start and end dates.")
            return self.get(request, *args, **kwargs)

        return HttpResponseRedirect(
            reverse(
                "web:daybook",  # Adjust the URL name as per your URL configuration
                kwargs={
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
        )


from datetime import date


class DayBookView(LoginRequiredMixin, View):
    def get(self, request, start_date, end_date):
        # Parse start and end dates
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        # Fetch company details
        company_details = Table_Companydetailsmaster.objects.first()

        # Fetch entries within the date range
        voucher_entries = Table_Voucher.objects.filter(Vdate__range=[start_date, end_date]).order_by("Vdate")
        drcr_entries = Table_DrCrNote.objects.filter(ndate__range=[start_date, end_date]).order_by("ndate")
        journal_entries = Table_Journal_Entry.objects.filter(vdate__range=[start_date, end_date]).order_by("vdate")
        contra_entries = Table_Contra_Entry.objects.filter(vdate__range=[start_date, end_date]).order_by("vdate")

        # Combine and sort all entries by date
        combined_entries = (
            list(voucher_entries) + list(drcr_entries) + list(journal_entries) + list(contra_entries)
        )
        combined_entries.sort(key=lambda x: getattr(x, 'Vdate', getattr(x, 'ndate', getattr(x, 'vdate', date.min))))

        # Process and calculate debit, credit, and balances for display
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        entry_list = []

        # Loop through the entries and process each one
        for entry in combined_entries:
            entry_dict = {}

            if hasattr(entry, "Vdate"):  # Table_Voucher entry
                debit_amount = Decimal(entry.VAmount or "0.00") if entry.CStatus == "P" else Decimal("0.00")
                credit_amount = Decimal(entry.VAmount or "0.00") if entry.CStatus == "R" else Decimal("0.00")
                account = Table_Accountsmaster.objects.filter(account_code=entry.Accountcode).first()
                head = account.head if account else "Unknown"
                entry_dict = {
                    "date": entry.Vdate,
                    "head": head,
                    "voucher_number": entry.VoucherNo or entry.Series,
                    "narration": entry.Narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "type": entry.CStatus,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }
                if entry.Headcode:
                    try:
                        head_account = Table_Accountsmaster.objects.get(account_code=entry.Headcode)
                
                        # Append 'Book Head' and current balance row only once
                        if entry.CStatus == 'P':
                            # Add 'Book Head' debit and credit to totals
                            total_debit += Decimal("0.00")  # For 'P' entries, we display in the credit column
                            total_credit += debit_amount  # Accumulate the correct amount for payments
                
                            # Show current balance in the credit column for payment entry
                            entry_list.append({
                                "date": entry.Vdate,
                                "head": head_account.head,
                                "voucher_number": entry.VoucherNo or entry.Series,
                                "narration": "",
                                "debit": Decimal("0.00"),  # No debit for payments
                                "credit": debit_amount,  # Show in credit for payments
                                "type": entry.CStatus,
                                "is_journal_entry": False,
                                "is_contra_entry": False,
                            })
                        elif entry.CStatus == 'R':
                            # Add 'Book Head' debit and credit to totals
                            total_debit += credit_amount  # Accumulate the correct amount for receipts
                            total_credit += Decimal("0.00")  # For 'R' entries, we display in the debit column
                
                            # Show current balance in the debit column for receipt entry
                            entry_list.append({
                                "date": entry.Vdate,
                                "head": head_account.head,
                                "voucher_number": entry.VoucherNo or entry.Series,
                                "narration": "",
                                "debit": credit_amount,  # Show in debit for receipts
                                "credit": Decimal("0.00"),  # No credit for receipts
                                "type": entry.CStatus,
                                "is_journal_entry": False,
                                "is_contra_entry": False,
                            })
                    except Table_Accountsmaster.DoesNotExist:
                        print(f"Headcode {entry.Headcode} not found in Table_Accountsmaster.")



            elif hasattr(entry, "ndate"):  # Table_DrCrNote entry
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                if entry.ntype == 'C':  # Credit Note
                    debit_amount, credit_amount = credit_amount, debit_amount
                account = Table_Accountsmaster.objects.filter(account_code=entry.accountcode).first()
                head = account.head if account else "Unknown"
                entry_dict = {
                    "date": entry.ndate,
                    "head": head,
                    "voucher_number": entry.noteno or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "type": entry.ntype,
                    "is_journal_entry": False,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Journal_Entry):
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                account = Table_Accountsmaster.objects.filter(account_code=entry.accountcode).first()
                head = account.head if account else "Unknown"
                entry_dict = {
                    "date": entry.vdate,
                    "head": head,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "type": 'Journal',
                    "is_journal_entry": True,
                    "is_contra_entry": False,
                }

            elif isinstance(entry, Table_Contra_Entry):
                debit_amount = Decimal(entry.dramount or "0.00")
                credit_amount = Decimal(entry.cramount or "0.00")
                account = Table_Accountsmaster.objects.filter(account_code=entry.accountcode).first()
                head = account.head if account else "Unknown"
                entry_dict = {
                    "date": entry.vdate,
                    "head": head,
                    "voucher_number": entry.voucher_no or entry.series,
                    "narration": entry.narration,
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "type": 'Contra',
                    "is_journal_entry": False,
                    "is_contra_entry": True,
                }

            # Accumulate totals
            total_debit += entry_dict.get("debit", Decimal("0.00"))
            total_credit += entry_dict.get("credit", Decimal("0.00"))
            entry_list.append(entry_dict)

        # Context for rendering the template
        context = {
            "entries": entry_list,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "start_date": start_date,
            "end_date": end_date,
            "company_name": company_details.companyname,
            "company_phone": company_details.phoneno,
            "company_address": company_details.address1,
            "company_gst": company_details.gst,
        }

        return render(request, "web/accounts/day-book/daybook.html", context)




from django.db.models import Sum

from django.db.models import Sum
from decimal import Decimal

from decimal import Decimal
from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Table_Companydetailsmaster, Table_Accountsmaster, Table_Voucher, Table_DrCrNote, Table_Journal_Entry, Table_Contra_Entry
import datetime

class TrialBalanceView(LoginRequiredMixin, View):
    def get(self, request):
        # Fetch company details
        company_details = Table_Companydetailsmaster.objects.first()

        # Fetch all accounts grouped by their group in Table_Accountsmaster
        accounts = Table_Accountsmaster.objects.all().order_by('group', 'head')

        # Fetch all entries without date filtering
        voucher_entries = Table_Voucher.objects.all().order_by("Vdate")
        drcr_entries = Table_DrCrNote.objects.all().order_by("ndate")
        journal_entries = Table_Journal_Entry.objects.all().order_by("vdate")
        contra_entries = Table_Contra_Entry.objects.all().order_by("vdate")

        # Combine and sort all entries by date
        combined_entries = (
            list(voucher_entries) + list(drcr_entries) + list(journal_entries) + list(contra_entries)
        )
        combined_entries.sort(key=lambda x: getattr(x, 'Vdate', getattr(x, 'ndate', getattr(x, 'vdate', datetime.datetime.min.date()))))

        # Initialize totals
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        entry_list = []
        group_totals = {}

        # Process and calculate debit, credit, and balances for display
        for account in accounts:
            # Ensure currentbalance is a Decimal
            current_balance = Decimal(account.currentbalance) if account.currentbalance not in [None, ''] else Decimal("0.00")
            
            # Initialize debit and credit for each account
            account_debit = Decimal("0.00")
            account_credit = Decimal("0.00")

            # Filter entries for this account and calculate debit/credit totals
            for entry in combined_entries:
                if hasattr(entry, "Accountcode") and entry.Accountcode == account.account_code:
                    debit_amount = Decimal(entry.VAmount or "0.00") if entry.CStatus == "P" else Decimal("0.00")
                    credit_amount = Decimal(entry.VAmount or "0.00") if entry.CStatus == "R" else Decimal("0.00")
                    account_debit += debit_amount
                    account_credit += credit_amount
                elif hasattr(entry, "accountcode") and entry.accountcode == account.account_code:
                    debit_amount = Decimal(entry.dramount or "0.00")
                    credit_amount = Decimal(entry.cramount or "0.00")
                    account_debit += debit_amount
                    account_credit += credit_amount

            # Update the totals
            total_debit += account_debit
            total_credit += account_credit

            # Add entry for this account with current balance
            entry_list.append({
                "group": account.group,
                "head": account.head,
                "current_balance": current_balance,
                "debit": account_debit,
                "credit": account_credit,
            })

            # Aggregate group totals
            if current_balance > 0:
                group_totals.setdefault(account.group, {'debit': Decimal("0.00"), 'credit': Decimal("0.00")})
                group_totals[account.group]['debit'] += current_balance
            elif current_balance < 0:
                group_totals.setdefault(account.group, {'debit': Decimal("0.00"), 'credit': Decimal("0.00")})
                group_totals[account.group]['credit'] += abs(current_balance)

        # Add group totals to entry list, updating the existing group entries
        for group, totals in group_totals.items():
            for entry in entry_list:
                if entry["group"] == group:
                    entry["debit"] += totals['debit']  # Add group total to debit column
                    entry["credit"] += totals['credit']  # Add group total to credit column
                    break

        # Context for rendering the template
        total_group_debit = sum(entry["debit"] for entry in entry_list)
        total_group_credit = sum(entry["credit"] for entry in entry_list)
        
        # Context for rendering the template
        context = {
            "entries": entry_list,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "total_group_debit": total_group_debit,
            "total_group_credit": total_group_credit,
            "company_name": company_details.companyname,
            "company_phone": company_details.phoneno,
            "company_address": company_details.address1,
            "company_gst": company_details.gst,
        }
        

        return render(request, "web/accounts/trial-balance/trialbalance.html", context)




# ----------------------------------------X---------------------X-------------------------------- #
# ----------------------------------------| ACCOUNTING END |------------------------------------- #
# ----------------------------------------X---------------------X---------------------------------#


import json
from django.http import JsonResponse

def csp_report_view(request):
    if request.method == 'POST':
        try:
            # Decode the JSON payload
            report = json.loads(request.body.decode('utf-8'))
            print("CSP Violation Report:", report)  # Log the report
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def render_button(request):
    return render(request, 'web/js-test.html') 

