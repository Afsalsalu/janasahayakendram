# Django imports for views, request handling, and authentication
import json
import random
import string
import uuid
from datetime import date

import pdfkit
# Third-party imports for payment integration and email handling
import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
# from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import IntegrityError
# from easy_pdf.views import PDFView
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from sib_api_v3_sdk import ApiClient, Configuration
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

# Custom imports for user forms and email utilities
from web.forms import CentreUserForm
from web.models import CentreUserAccount

from .constants import PaymentStatus
# Django imports for models, forms, and utility functions
from .forms import UserRegistrationForm
from .models import (ExamCategory, MainExamOption, MainExamProgress,
                     MainExamQuestion, Option, Payment, Question,
                     TecExamProgress, UserRegistration, VideoRecord)


class UserRegistrationMixin:
    """
    A mixin to handle user registration-specific data in class-based views.

    This mixin provides utility methods to retrieve the `UserRegistration`
    instance associated with the currently logged-in user and to filter querysets
    based on the user's registration details.
    """

    def get_user_registration(self):
        """
        Retrieve the `UserRegistration` instance for the currently logged-in user.

        Returns:
            UserRegistration: The `UserRegistration` instance associated with the current user.

        Raises:
            Http404: If the `UserRegistration` instance does not exist for the current user.
        """
        return get_object_or_404(UserRegistration, user=self.request.user)

    def get_queryset(self):
        """
        Filter the queryset to include only objects related to the current user's registration.

        This method overrides the base `get_queryset` method to filter the queryset
        based on the current user's registration details. It ensures that only data
        pertinent to the user's registration is included in the queryset.

        Returns:
            QuerySet: A filtered queryset containing only objects related to the current user's registration.
        """
        qs = super().get_queryset()  # Call the parent class's get_queryset method.
        return qs.filter(
            user_registration=self.get_user_registration()
        )  # Filter the queryset.


# View to handle user registration
class UserRegistrationView(UserRegistrationMixin, View):
    def get(self, request):
        # Display the user registration form
        form = UserRegistrationForm()
        return render(request, "web/exam/register.html", {"form": form})

    def post(self, request):
        # Handle form submission for user registration
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.cleaned_data
            mobile = form_data.get("mobile")

            # Save file and get the file path
            photo = request.FILES.get("photo")
            if photo:
                photo_path = default_storage.save(
                    f"photos/{photo.name}", ContentFile(photo.read())
                )
                form_data["photo"] = photo_path

            # Convert date fields to string format before storing in session
            for key, value in form_data.items():
                if isinstance(value, date):
                    form_data[key] = value.strftime("%Y-%m-%d")

            # Store form data in session for later use
            request.session["form_data"] = form_data
            request.session["razorpay_order_id"] = None  # Reset Razorpay order ID

            # Initiate payment through Razorpay
            try:
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                payment = client.order.create(
                    {
                        "amount": 100,  # Amount in paisa (100 INR)
                        "currency": "INR",
                        "payment_capture": 1,
                    }
                )

                # Store payment details in session
                request.session["razorpay_order_id"] = payment["id"]

                # Render payment page with Razorpay details
                return render(
                    request,
                    "web/exam/payment.html",
                    {
                        "payment": payment,
                        "mobile": mobile,
                        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                    },
                )
            except Exception as e:
                # Handle payment initiation errors
                form.add_error(None, "Error initiating payment. Please try again.")
                print("Payment initiation error:", e)
        else:
            # Handle form validation errors
            print("Form errors:", form.errors)

        # Render registration page with form errors
        return render(request, "web/exam/register.html", {"form": form})


# View to handle payment callback from Razorpay
@method_decorator(csrf_exempt, name="dispatch")
class PaymentCallbackView(UserRegistrationMixin, View):
    def post(self, request):
        # Process payment callback from Razorpay
        payment_data = request.POST
        razorpay_order_id = payment_data.get("razorpay_order_id")

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": payment_data["razorpay_payment_id"],
                "razorpay_signature": payment_data["razorpay_signature"],
            }

            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)

            # Payment is successful; save form data and create user
            form_data = request.session.get("form_data")
            photo_filename = request.session.get("photo")

            if not form_data:
                print("Session data not found.")
                return redirect("exam:entrepreneur_register")

            # Handle photo file
            if photo_filename:
                # Recreate the InMemoryUploadedFile object
                uploaded_file = request.FILES.get(photo_filename)
                # Save the file using Django's default file storage
                photo_path = default_storage.save(
                    f"photos/{photo_filename}", ContentFile(uploaded_file.read())
                )

                # Update the form data with the file path
                form_data["photo"] = photo_path

            # Create UserRegistration object
            user_registration = UserRegistration(**form_data)
            username = self.generate_unique_username(user_registration.mobile[:8])
            password = user_registration.mobile

            try:
                # Create user account
                User = get_user_model()
                user = User.objects.create_user(username=username, password=password)
                user_registration.user = user
                user_registration.save()

                # Record payment details
                Payment.objects.create(
                    user_registration=user_registration,
                    amount=100,  # Amount in INR
                    provider_order_id=razorpay_order_id,
                    status=PaymentStatus.SUCCESS,
                    payment_id=payment_data["razorpay_payment_id"],
                    signature_id=payment_data["razorpay_signature"],
                )

                # Clear session data
                request.session.pop("form_data", None)
                request.session.pop("razorpay_order_id", None)
                request.session.pop("photo", None)

                # Send a welcome email to the user
                self.send_welcome_email(user_registration)

                return redirect("exam:entrepreneur_userlogin")
            except IntegrityError as e:
                # Handle user creation errors
                print("Integrity error:", e)
                return redirect("exam:entrepreneur_register")
        except Exception as e:
            # Handle payment verification errors
            print("Payment verification failed:", e)
            try:
                payment = Payment.objects.get(provider_order_id=razorpay_order_id)
                payment.status = PaymentStatus.FAILURE
                payment.save()
            except Payment.DoesNotExist:
                print("Payment record not found.")
            return redirect("exam:entrepreneur_register")

    def generate_unique_username(self, base_username):
        # Generate a unique username with a prefix and random suffix if needed
        prefix = "TEC"
        base_username = (
            f"{prefix}{base_username[:8]}"  # Limit base username to 8 characters
        )
        User = get_user_model()
        username = base_username
        while User.objects.filter(username=username).exists():
            suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=8)
            )
            username = f"{base_username}{suffix}"
        return username

    def send_welcome_email(self, user_registration):
        # Prepare and send a welcome email to the new user
        subject = "Welcome to the Samatwa Service Centre E-Governance LTD"
        html_content = (
            f"<p>Thank you for registering. Your account has been created successfully.</p>"
            f"<p><strong>Centre ID:</strong> {user_registration.id}</p>"
            f"<p><strong>Username:</strong> {user_registration.user.username}</p>"
            f"<p><strong>Password:</strong> {user_registration.mobile}</p>"
            f"<p>We recommend you change your password after logging in.</p>"
            f"<p>For more information, visit our website: <a href='https://sscegov.com'>https://sscegov.com</a></p>"
            f"<p>Best regards,<br>The SSC Team</p>"
        )

        configuration = Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_client = ApiClient(configuration)
        api_instance = transactional_emails_api.TransactionalEmailsApi(api_client)

        email_data = SendSmtpEmail(
            to=[{"email": user_registration.email}],
            subject=subject,
            html_content=html_content,
            sender={
                "name": "Samatwa Service Centre",
                "email": "samatwaservicecenter.gov.in@gmail.com",
            },
        )

        try:
            api_response = api_instance.send_transac_email(email_data)
            print("Email sent successfully:", api_response)
        except ApiException as e:
            print("Exception when sending email: %s\n" % e)


def login_view(request):
    if request.method == "POST":
        # Retrieve username and password from the POST request
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate the user with the provided credentials
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in
            auth_login(request, user)
            # Redirect the user to the dashboard
            return redirect("exam:dashboard")
        else:
            # If authentication fails, display an error message
            messages.error(request, "Invalid username or password")

    # Render the login page if the request method is not POST
    return render(request, "web/exam/userlogin.html")


def logout_view(request):
    # Log out the user and clear session data
    logout(request)
    # Redirect the user to the login page
    return redirect("exam:entrepreneur_userlogin")
 

# @login_required
def admin_dashboard(request):
    # Retrieve the currently logged-in user
    user = request.user

    # Get the user's profile from the UserRegistration model
    profile = UserRegistration.objects.filter(user=user).first()

    if not profile:
        # If profile does not exist, redirect to profile creation page
        return redirect("exam:details_entry")

    # Retrieve the user's exam progress, ordered by the most recent attempt
    progress = MainExamProgress.objects.filter(user=user).order_by("-attempt_number")
    last_attempt = progress.first() if progress.exists() else None

    # Determine the certificate status based on the exam progress
    if not progress.exists():
        certificate_status = (
            "Exam not attempted. Please complete the assessment and take the exam."
        )
        payment_button = None
    elif last_attempt.status == "Passed":
        if profile.certificate_paid:
            certificate_status = (
                "Certificate payment successful. Download your certificate anytime."
            )
            payment_button = None
        else:
            certificate_status = "Congratulations! You have passed the exam. Please complete your details to pay for the certificate."
            payment_button = profile.details_filled
    elif last_attempt.status == "Failed Attempt 1":
        if last_attempt.attempt_number == 1:
            certificate_status = "Your 1st attempt failed. You have only 1 chance remaining. Better luck on the 2nd attempt!"
        else:
            certificate_status = "You have failed on the 1st attempt. Please review the material and try again."
        payment_button = None
    elif last_attempt.status == "Failed Attempt 2":
        certificate_status = "You have failed the exam twice. The exam is frozen. No more chances available. Sorry!"
        payment_button = None
    else:
        certificate_status = (
            "Exam not attempted. Please complete the assessment to take the exam."
        )
        payment_button = None

    # Prepare context data for rendering the dashboard template
    context = {
        "profile": profile,
        "progress": progress,
        "certificate_status": certificate_status,
        "payment_button": payment_button,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,  # Pass the Razorpay Key ID to the template
    }

    # Render the dashboard template with the context data
    return render(request, "web/exam/dashboard.html", context)


# @login_required
def learning(request):
    # Retrieve all exam categories
    questions = ExamCategory.objects.all()

    # Render the learning page with the exam categories
    return render(request, "web/exam/learning.html", {"questions": questions})


# @login_required
def assessments(request):
    user = request.user
    user_registration = get_object_or_404(UserRegistration, user=user)

    # Retrieve all exam categories
    exams = ExamCategory.objects.all()

    # Fetch progress data for the current user
    progress_data = TecExamProgress.objects.filter(
        user=user_registration
    ).select_related("exam_category")

    # Convert progress data into a dictionary for easy access
    progress_dict = {p.exam_category.id: p for p in progress_data}

    # Prepare a list to store progress information
    progress_list = []

    all_exams_passed = True  # Assume all exams are passed initially

    for index, exam in enumerate(exams):
        exam_progress = progress_dict.get(exam.id)
        total_questions = Question.objects.filter(exam_category=exam).count()
        correct_answers = exam_progress.correct_answers if exam_progress else None

        # Determine the status of the current exam
        if index == 0:
            # First exam's status is determined based on its progress
            if exam_progress:
                status = (
                    exam_progress.status.capitalize()
                    if exam_progress.status
                    else "Open"
                )
            else:
                status = (
                    "Open"  # Assuming we want the first exam open if no progress exists
                )
        else:
            # Check the status of the previous exam
            previous_exam = exams[index - 1]
            previous_progress = progress_dict.get(previous_exam.id)

            if previous_progress and previous_progress.status == "Passed":
                status = (
                    "Open" if not exam_progress else exam_progress.status.capitalize()
                )
            else:
                status = "Locked"
                all_exams_passed = (
                    False  # Mark as False if any exam is locked or not passed
                )

        # Append exam progress information to the list
        progress_list.append(
            {
                "exam_name": exam.name,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "status": status,
                "exam_id": exam.id,
            }
        )

    # Render the assessments page with progress data
    return render(
        request,
        "web/exam/assessments.html",
        {
            "progress_data": progress_list,
            "all_exams_passed": all_exams_passed,
        },
    )


# @login_required
def take_exam(request, exam_id):
    exam_category = get_object_or_404(ExamCategory, id=exam_id)
    user = request.user
    user_registration = get_object_or_404(UserRegistration, user=user)

    # Get or create a progress record for this user and exam category
    progress, created = TecExamProgress.objects.get_or_create(
        user=user_registration, exam_category=exam_category
    )

    # Prevent retaking the exam if the status is 'Passed' or 'Locked'
    if progress.status in ["Passed", "Locked"]:
        messages.error(request, "You cannot retake this exam.")
        return redirect("exam:assessments")

    questions = Question.objects.filter(exam_category=exam_category).prefetch_related(
        "options"
    )
    if not questions.exists():
        messages.error(request, "No questions available for this exam.")
        return redirect("exam:assessments")

    if request.method == "POST":
        user_answers = {}
        correct_count = 0
        for question in questions:
            answer_id = request.POST.get(f"question_{question.id}")
            if answer_id:
                user_answers[question.id] = answer_id
                if Option.objects.filter(
                    id=answer_id, question=question, is_correct=True
                ).exists():
                    correct_count += 1

        total_questions = len(questions)
        score = correct_count  # Score is the number of correct answers

        # Update the progress record with the user's answers, score, and status
        update_user_progress(user, exam_category, score)

        # Redirect to the assessments page after saving the progress
        return redirect("exam:assessments")

    context = {
        "exam_category": exam_category,
        "questions": questions,
        "progress": progress,
    }
    return render(request, "web/exam/exam/take_exam.html", context)


def update_user_progress(user, exam_category, score):
    """
    Update user's progress for the exam category based on score.
    """
    user_registration = get_object_or_404(UserRegistration, user=user)
    user_progress, created = TecExamProgress.objects.get_or_create(
        user=user_registration, exam_category=exam_category
    )

    # Passing mark is 5 correct answers
    user_progress.score = score
    user_progress.status = "Passed" if score >= 5 else "Failed"
    user_progress.correct_answers = score  # Correct answers count
    user_progress.save()


def calculate_score(questions, user_answers):
    """
    Calculate the number of correct answers based on user responses.
    """
    correct_answers = 0
    for question in questions:
        if question.id in user_answers:
            selected_option_id = user_answers[question.id]
            if Option.objects.filter(
                id=selected_option_id, question=question, is_correct=True
            ).exists():
                correct_answers += 1
    return correct_answers  # Return the count of correct answers


# @login_required
def main_exam(request):
    MAX_ATTEMPTS = 3
    PASSING_SCORE_PERCENTAGE = 70  # Example: 70% required to pass

    if request.method == "POST":
        user = request.user
        submitted_answers = request.POST

        # Fetch all questions from the MainExamQuestion model
        questions = MainExamQuestion.objects.all()
        total_questions = questions.count()
        correct_answers_count = 0

        # Evaluate the user's answers
        for question in questions:
            selected_option_id = submitted_answers.get(f"question_{question.id}")
            if selected_option_id:
                try:
                    selected_option = MainExamOption.objects.get(id=selected_option_id)
                    if selected_option.is_correct:
                        correct_answers_count += 1
                except MainExamOption.DoesNotExist:
                    pass  # Skip invalid options

        # Calculate the user's score percentage
        score_percentage = (correct_answers_count / total_questions) * 100
        passed = score_percentage >= PASSING_SCORE_PERCENTAGE

        # Fetch user's previous attempts to check if they can take the exam again
        previous_attempts = MainExamProgress.objects.filter(user=user).order_by(
            "-attempt_number"
        )
        attempt_number = 1
        if previous_attempts.exists():
            last_attempt = previous_attempts.first()
            if last_attempt.status == "Passed":
                messages.info(request, "You have already passed the exam.")
                return redirect("exam:dashboard")
            elif last_attempt.attempt_number >= MAX_ATTEMPTS:
                messages.error(
                    request, "You have reached the maximum number of attempts."
                )
                return redirect("exam:dashboard")
            else:
                attempt_number = last_attempt.attempt_number + 1

        # Save the exam attempt details
        MainExamProgress.objects.create(
            user=user,
            attempt_number=attempt_number,
            correct_answers=correct_answers_count,
            total_questions=total_questions,
            status="Passed" if passed else f"Failed Attempt {attempt_number}",
            completed_at=timezone.now(),
        )

        # Prepare feedback messages based on the result
        if passed:
            messages.success(
                request,
                f"Congratulations! You passed the exam with a score of {score_percentage:.2f}%.",
            )
        else:
            remaining_attempts = MAX_ATTEMPTS - attempt_number
            if remaining_attempts > 0:
                messages.warning(
                    request,
                    f"You scored {score_percentage:.2f}%. You did not pass the exam. You have {remaining_attempts} attempt(s) remaining.",
                )
            else:
                messages.error(
                    request,
                    f"You scored {score_percentage:.2f}%. You have used all your attempts.",
                )

        return redirect("exam:dashboard")

    else:
        # Check if the user has remaining attempts
        user = request.user
        previous_attempts = MainExamProgress.objects.filter(user=user).order_by(
            "-attempt_number"
        )
        if previous_attempts.exists():
            last_attempt = previous_attempts.first()
            if last_attempt.status == "Passed":
                messages.info(request, "You have already passed the exam.")
                return redirect("exam:dashboard")
            elif last_attempt.attempt_number >= MAX_ATTEMPTS:
                messages.error(
                    request, "You have reached the maximum number of attempts."
                )
                return redirect("exam:dashboard")

        # Fetch and display all questions with options
        questions = MainExamQuestion.objects.prefetch_related("options").all()

        return render(request, "web/exam/main_exam.html", {"questions": questions})


# @login_required
@csrf_exempt
def submit_exam(request):
    if request.method == "POST":
        user = request.user
        submitted_answers = request.POST

        # Fetch all questions from the MainExamQuestion model
        questions = MainExamQuestion.objects.all()
        total_questions = questions.count()
        correct_answers_count = 0

        # Evaluate the user's answers
        for question in questions:
            selected_option_id = submitted_answers.get(f"question_{question.id}")
            if selected_option_id:
                try:
                    selected_option = MainExamOption.objects.get(id=selected_option_id)
                    if selected_option.is_correct:
                        correct_answers_count += 1
                except MainExamOption.DoesNotExist:
                    pass  # Skip invalid options

        # Calculate the user's score percentage
        score_percentage = (correct_answers_count / total_questions) * 100
        passed = score_percentage >= 70  # Assuming 70% is the passing score

        # Fetch or create a progress record for the user
        progress, created = MainExamProgress.objects.get_or_create(user=user)
        attempt_number = progress.attempt_number + 1 if not created else 1

        if attempt_number > 3:
            return JsonResponse(
                {
                    "success": False,
                    "message": "You have reached the maximum number of attempts.",
                },
                status=400,
            )

        # Update progress
        progress.update_progress(correct_answers_count, attempt_number)

        return JsonResponse(
            {
                "success": True,
                "score": score_percentage,
                "pass_exam": passed,
                "redirect_url": "/exam/dashboard/",
            },
            status=200,
        )

    return JsonResponse(
        {"success": False, "message": "Invalid request method."}, status=400
    )


@csrf_exempt
def save_video(request):
    if request.method == "POST":
        video_file = request.FILES.get("video_file")
        if video_file:
            user = request.user
            user_registration = UserRegistration.objects.get(user=user)

            # Save the video file
            filename = f"{user.username}_{uuid.uuid4()}.webm"
            video_record = VideoRecord(
                user_registration=user_registration, video_file=video_file
            )
            video_record.save()

            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"success": False, "message": "No video file uploaded."}, status=400
            )
    return JsonResponse(
        {"success": False, "message": "Invalid request method."}, status=400
    )


# @login_required
@csrf_exempt
def certificate_payment(request):
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
        profile = UserRegistration.objects.get(user=request.user)
        # Mark the certificate as paid
        profile.certificate_paid = True
        profile.save()

        # Record the payment details in the Payment model
        Payment.objects.create(
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


# @login_required
def download_certificate(request):
    # Retrieve the user registration profile
    profile = UserRegistration.objects.get(user=request.user)

    # Check if the certificate payment has been made
    if profile.certificate_paid:
        # Path to the generated certificate file (PDF)
        certificate_file_path = "/path/to/generated/certificate.pdf"

        # Open the certificate file and prepare a response
        with open(certificate_file_path, "rb") as pdf:
            response = HttpResponse(pdf.read(), content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="certificate.pdf"'
            return response
    else:
        # If payment has not been made, show an error message and redirect to the dashboard
        messages.error(request, "You must pay for the certificate before downloading.")
        return redirect("exam:dashboard")


# Get the custom user model from the `web` app
User = get_user_model()


def generate_username():
    """
    Generate a unique username that does not exist in the database.
    """
    while True:
        # Generate a 12-digit random username
        username = "".join([str(random.randint(0, 9)) for _ in range(12)])

        # Check if the username already exists in the custom user model
        if not User.objects.filter(username=username).exists():
            return username


# @login_required
def details_entry(request):
    # Attempt to retrieve or create a UserRegistration object for the current user
    user_registration, created = UserRegistration.objects.get_or_create(
        user=request.user
    )

    # If the user registration details are already filled, redirect to the dashboard
    if user_registration.details_filled:
        return redirect("exam:dashboard")

    # Handle form submission
    if request.method == "POST":
        # Create a form instance with POST data and files
        form = CentreUserForm(request.POST, request.FILES, request=request)

        # Check if the form is valid
        if form.is_valid():
            # Save the form data, but do not commit to the database yet
            centre_user = form.save(commit=False)

            # Generate a unique username
            username = generate_username()
            password = str(
                centre_user.mobile
            )  # Use the user's mobile number as the password

            # Create a new user with the generated username, password, and email
            user = User.objects.create_user(
                username=username,
                password=password,
                email=centre_user.email,  # Assuming the email field is filled in the form
            )

            # Set the user type to 'centre' and save the user
            user.usertype = "centre"
            user.save()

            # Assign the created user to the form instance and save it to the database
            centre_user.user = user
            centre_user.save()

            # Mark the user registration details as filled
            user_registration.details_filled = True
            user_registration.save()

            # Create a CentreUserAccount for the user
            centre_user_account = CentreUserAccount.objects.create(
                user=user,
                username=username,
                owner_centre=centre_user.centre_name,
                mobile=centre_user.mobile,
                # Add other fields as needed
            )

            # Access the formatted ID from the CentreUserAccount instance
            formatted_id = centre_user_account.formatted_id

            # Send a welcome email to the user with the credentials and formatted ID
            subject = "Welcome to the Samatwa Service Centre E-Governance LTD"
            html_content = (
                f"<p>Thank you for registering. Your account has been created successfully.</p>"
                f"<p><strong>Centre ID:</strong> {formatted_id}</p>"
                f"<p><strong>Username:</strong> {username}</p>"
                f"<p><strong>Password:</strong> {password}</p>"
                f"<p>We recommend you change your password after logging in.</p>"
                f"<p>For more information, visit our website: <a href='https://sscegov.com'>https://sscegov.com</a></p>"
                f"<p>Best regards,<br>The SSC Team</p>"
            )

            configuration = Configuration()
            configuration.api_key["api-key"] = settings.BREVO_API_KEY

            api_client = ApiClient(configuration)
            api_instance = transactional_emails_api.TransactionalEmailsApi(api_client)

            email_data = SendSmtpEmail(
                to=[{"email": centre_user.email}],
                subject=subject,
                html_content=html_content,
                sender={
                    "name": "Samatwa Service Centre",
                    "email": "samatwaservicecenter.gov.in@gmail.com",
                },
            )

            try:
                api_response = api_instance.send_transac_email(email_data)
                print("Email sent successfully:", api_response)
            except ApiException as e:
                print(f"Exception when sending email: {e}\n")

            # Redirect to the dashboard after successful form submission
            return redirect("exam:dashboard")
    else:
        # Create a form instance for GET request
        form = CentreUserForm(request=request)

    # Render the details entry page with the form instance
    return render(request, "web/exam/details_entry.html", {"form": form})


class CertificateView(View):
    def get(self, request, *args, **kwargs):
        user_registration = get_object_or_404(UserRegistration, user=request.user)

        # Check if the user is authorized to view/download the certificate
        if (
            not user_registration.all_main_exams_passed()
            or not user_registration.certificate_paid
            or user_registration.certificate_downloaded
        ):
            return HttpResponseForbidden(
                "You are not authorized to view or download this certificate."
            )

        # Use Django's static file handling to get the image URL
        image_url = request.build_absolute_uri(static("web/images/certificate.jpg"))

        # Render the HTML template with context data
        html_string = render_to_string(
            "web/certificate-pdf.html",
            {
                "content": user_registration.name,
                "shop_name": user_registration.another_name,
                "district": user_registration.district,
                "created": user_registration.registration_date,
                "image_url": image_url,
            },
        )

        # Specify the full path to wkhtmltopdf
        path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # Generate PDF from the HTML string
        pdf = pdfkit.from_string(html_string, False, configuration=config)

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


def test(request):
    return render(request, "web/exam/test.html")

