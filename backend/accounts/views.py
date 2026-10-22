import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
)

from accounts.permissions import IsAdmin
from accounts.models import Profile
from dashboard.models import ActivityLog


User = get_user_model()


# ============================================================
# JWT TOKENS
# ============================================================

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ============================================================
# OTP HELPERS
# ============================================================

OTP_EXPIRY_SECONDS = 90


def generate_otp():
    """
    Generate a secure 6-digit OTP.
    """
    return f'{random.SystemRandom().randint(0, 999999):06d}'


def otp_cache_key(email):
    """
    Unique cache key for each email.
    """
    return f'secondlife_registration_otp_{email.lower().strip()}'


def send_registration_otp(email, name):
    """
    Generate and send a 6-digit registration OTP.
    OTP is valid for 90 seconds.
    """

    email = email.lower().strip()

    otp = generate_otp()

    cache.set(
        otp_cache_key(email),
        otp,
        timeout=OTP_EXPIRY_SECONDS
    )

    subject = 'Second Life - Your Verification Code'

    message = f"""Hello {name},

Welcome to Second Life! 🌱

Your Second Life verification code is:

{otp}

This code will expire in 90 seconds.

Please enter this verification code on the Second Life registration page to verify your email address.

If you did not create a Second Life account, you can safely ignore this email.

Regards,
Second Life Team
"""

    from services.email_service import send_platform_email
    sent = send_platform_email(email, subject, message)
    if not sent:
        raise RuntimeError(
            'Registration OTP email could not be sent. Check the Brevo API key and verified sender configuration.'
        )
    return otp


# ============================================================
# REGISTER
# ============================================================

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save()

        except IntegrityError:
            return Response(
                {
                    'email': [
                        'This email is already registered.'
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_verified = False
        user.save(update_fields=['is_verified'])

        try:
            send_registration_otp(
                user.email,
                user.name
            )

        except Exception as error:

            print(
                'Registration OTP email error:',
                error
            )

            user.delete()

            return Response(
                {
                    'error': (
                        'Unable to send verification email. '
                        'Please check your email configuration '
                        'and try again.'
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'message': (
                    'Registration details saved. '
                    'A 6-digit OTP has been sent to your email.'
                ),
                'otp_required': True,
                'email': user.email,
                'expires_in': OTP_EXPIRY_SECONDS,
            },
            status=status.HTTP_201_CREATED
        )


# ============================================================
# VERIFY REGISTRATION OTP
# ============================================================

class VerifyRegistrationOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        email = request.data.get(
            'email',
            ''
        ).strip().lower()

        otp = str(
            request.data.get(
                'otp',
                ''
            )
        ).strip()

        if not email:
            return Response(
                {
                    'error': 'Email address is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not otp:
            return Response(
                {
                    'error': 'Please enter the OTP.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(otp) != 6 or not otp.isdigit():
            return Response(
                {
                    'error': 'OTP must be exactly 6 digits.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:
            return Response(
                {
                    'error': (
                        'No registration found for this email.'
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {
                    'error': 'This account is already verified.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        stored_otp = cache.get(
            otp_cache_key(email)
        )

        if not stored_otp:
            return Response(
                {
                    'error': (
                        'OTP has expired. '
                        'Please request a new OTP.'
                    ),
                    'otp_expired': True,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if str(stored_otp) != otp:
            return Response(
                {
                    'error': 'Invalid OTP. Please try again.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_verified = True
        user.save(
            update_fields=['is_verified']
        )

        cache.delete(
            otp_cache_key(email)
        )

        try:
            from services.email_service import send_platform_email

            sent = send_platform_email(
                user.email,
                'Welcome to Second Life! 🌱',
                f"""Hello {user.name},

Welcome to Second Life! 🌱

Your email has been successfully verified and your Second Life account is now active.

You can now sign in and start using the platform.

Your account details:

Name: {user.name}
Email: {user.email}
Account Type: {getattr(user, 'account_type', 'User')}
Role: {getattr(user, 'role', 'User')}

Thank you for joining Second Life and helping us give useful items a second life.

Regards,
Second Life Team
""",
            )

            if not sent:
                print(
                    'Registration success email error: '
                    'Brevo could not accept the message.'
                )

        except Exception as error:
            print(
                'Registration success email error:',
                error
            )

        tokens = get_tokens_for_user(user)

        try:
            ActivityLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                description=(
                    f'User {user.name} '
                    f'({user.email}) completed email verification.'
                )
            )

        except Exception as error:
            print(
                'Activity log error:',
                error
            )

        return Response(
            {
                'message': 'Email verified successfully!',
                'tokens': tokens,
                'user': UserSerializer(
                    user,
                    context={
                        'request': request
                    }
                ).data,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# RESEND REGISTRATION OTP
# ============================================================

class ResendRegistrationOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        email = request.data.get(
            'email',
            ''
        ).strip().lower()

        if not email:
            return Response(
                {
                    'error': 'Email address is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:
            return Response(
                {
                    'error': (
                        'No registration found for this email.'
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {
                    'error': 'This account is already verified.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            send_registration_otp(
                user.email,
                user.name
            )

        except Exception as error:

            print(
                'Resend OTP email error:',
                error
            )

            return Response(
                {
                    'error': (
                        'Unable to send OTP email. '
                        'Please try again later.'
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'message': (
                    'A new OTP has been sent to your email.'
                ),
                'otp_required': True,
                'email': user.email,
                'expires_in': OTP_EXPIRY_SECONDS,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# LOGIN
# ============================================================

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        email = request.data.get(
            'email',
            ''
        ).strip().lower()

        password = request.data.get(
            'password',
            ''
        )

        if not email or not password:
            return Response(
                {
                    'error': (
                        'Please provide both '
                        'email and password.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            existing_user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:
            existing_user = None

        if existing_user and existing_user.is_verified and existing_user.account_type == User.AccountType.ORGANIZATION:
            try:
                organization = existing_user.organization
            except Exception:
                organization = None
            if organization and organization.verification_status != 'VERIFIED':
                if organization.verification_status == 'REJECTED':
                    message = 'Your organization registration was not approved. Please review the rejection reason or contact Second Life support.'
                else:
                    message = 'Your email is verified, but your organization registration is awaiting administrator approval. You can sign in after it is approved.'
                return Response({
                    'error': message,
                    'organization_pending': organization.verification_status == 'PENDING',
                    'organization_status': organization.verification_status,
                    'verification_reason': organization.verification_reason,
                }, status=status.HTTP_403_FORBIDDEN)

        if existing_user and not existing_user.is_verified:

            return Response(
                {
                    'error': (
                        'Please verify your email '
                        'before signing in.'
                    ),
                    'email_not_verified': True,
                    'email': existing_user.email,
                },
                status=status.HTTP_403_FORBIDDEN
            )

        user = authenticate(
            request,
            email=email,
            password=password
        )

        if not user:

            if existing_user and not existing_user.is_active:

                return Response(
                    {
                        'error': (
                            'This account has been '
                            'suspended by administration.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            return Response(
                {
                    'error': 'Invalid email or password.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:

            return Response(
                {
                    'error': (
                        'This account has been suspended.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = get_tokens_for_user(user)

        try:
            ActivityLog.objects.create(
                user=user,
                action='USER_LOGIN',
                description=(
                    f'User {user.name} '
                    f'({user.email}) logged in successfully.'
                )
            )

        except Exception as error:
            print(
                'Activity log error:',
                error
            )

        return Response(
            {
                'message': 'Login successful',
                'tokens': tokens,
                'user': UserSerializer(
                    user,
                    context={
                        'request': request
                    }
                ).data
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# CURRENT USER
# ============================================================

class MeView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        # Make sure every account has a profile object.
        Profile.objects.get_or_create(
            user=request.user
        )

        return Response(
            UserSerializer(
                request.user,
                context={
                    'request': request
                }
            ).data
        )

    def patch(self, request):

        # IMPORTANT:
        # ProfileUpdateSerializer is a User serializer.
        # Pass request.user, NOT request.user.profile.
        Profile.objects.get_or_create(
            user=request.user
        )

        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={
                'request': request
            }
        )

        if serializer.is_valid():

            updated_user = serializer.save()

            # Return the complete updated user so the frontend
            # AuthContext can immediately update its local state.
            return Response(
                UserSerializer(
                    updated_user,
                    context={
                        'request': request
                    }
                ).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# DELETE CURRENT ACCOUNT
# ============================================================

class DeleteAccountView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def delete(self, request):
        # Self-service deletion is intentionally limited to donor and
        # receiver accounts. Admin accounts must remain protected.
        if request.user.role not in (
            User.Role.DONOR,
            User.Role.RECEIVER,
        ):
            return Response(
                {'error': 'This account cannot be deleted from the application.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = request.user
        user.delete()

        return Response(
            {'message': 'Your account has been permanently deleted.'},
            status=status.HTTP_200_OK,
        )


# ============================================================
# PROFILE IMAGE UPLOAD
# ============================================================

class ProfileImageUploadView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

    def post(self, request):

        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        image = request.FILES.get('image')

        if not image:
            return Response(
                {
                    'error': 'No image was provided.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Backend image validation
        # ----------------------------------------------------

        if not image.content_type or image.content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
            return Response(
                {'error': 'Please upload a PNG, JPEG, or WebP image.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if image.size > self.MAX_IMAGE_SIZE:
            return Response(
                {
                    'error': 'Image size must be 5 MB or smaller.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        from PIL import Image, UnidentifiedImageError
        try:
            decoded = Image.open(image)
            if decoded.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Unsupported image format')
            decoded.verify()
            image.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            return Response(
                {'error': 'The uploaded file is not a valid image.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Save profile image
        # ----------------------------------------------------

        profile.image = image
        profile.save()

        # ----------------------------------------------------
        # Return COMPLETE updated user
        # ----------------------------------------------------
        # This is important because ReceiverSettings uses
        # updateUser(res.user), and the top-right avatar is
        # connected to the global AuthContext user object.

        user_data = UserSerializer(
            request.user,
            context={
                'request': request
            }
        ).data

        profile_data = user_data.get(
            'profile',
            {}
        )

        return Response(
            {
                'message': 'Profile image updated successfully.',
                'image': profile_data.get('image'),
                'user': user_data,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================

class ChangePasswordView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={
                'request': request
            }
        )

        if serializer.is_valid():

            request.user.set_password(
                serializer.validated_data['new_password']
            )

            request.user.save()

            return Response(
                {
                    'message': (
                        'Password changed successfully.'
                    )
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):

        email = request.data.get(
            'email',
            ''
        ).strip().lower()

        if not email:
            return Response(
                {
                    'error': 'Email address is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:

            return Response(
                {
                    'message': (
                        'If an account exists with this email, '
                        'a password reset link has been sent.'
                    )
                },
                status=status.HTTP_200_OK
            )

        from django.contrib.auth.tokens import (
            default_token_generator
        )

        token = default_token_generator.make_token(user)

        # Always use the server-configured frontend URL. A client must not
        # be able to redirect password-reset links to an arbitrary origin.
        frontend_url = getattr(
            settings,
            'FRONTEND_URL',
            'http://localhost:5173',
        ).strip().rstrip('/')

        reset_url = (
            f'{frontend_url}/reset-password'
            f'?uid={user.pk}'
            f'&token={token}'
        )

        subject = 'Second Life - Password Reset Request'

        message = f"""Hello {user.name},

We received a request to reset the password for your Second Life account.

You can reset your password by clicking the link below:

{reset_url}

This link is for your account only. If you did not request a password reset, you can safely ignore this email.

For your security, please do not share this link with anyone.

Regards,
Second Life Team
"""

        try:

            from services.email_service import send_platform_email

            if not send_platform_email(user.email, subject, message):
                raise RuntimeError('Brevo rejected or could not deliver the password reset email.')

            print(
                f'Password reset email sent successfully to {user.email}'
            )

        except Exception as error:

            print(
                'Password reset email error:',
                error
            )

            return Response(
                {
                    'error': (
                        'Unable to send password reset email. '
                        'Please try again later.'
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'message': (
                    'If an account exists with this email, '
                    'a password reset link has been sent.'
                )
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):

        from django.contrib.auth.tokens import (
            default_token_generator
        )

        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')

        if not uid or not token or not password:
            return Response(
                {
                    'error': (
                        'UID, token and password '
                        'are required.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(
                pk=uid
            )

        except User.DoesNotExist:

            return Response(
                {
                    'error': 'Invalid password reset request.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(
            user,
            token
        ):

            return Response(
                {
                    'error': (
                        'Password reset link is invalid '
                        'or has expired.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth.password_validation import validate_password

        try:
            validate_password(password, user=user)
        except Exception as error:
            return Response(
                {'error': error.messages[0] if getattr(error, 'messages', None) else 'Password does not meet security requirements.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save()

        return Response(
            {
                'message': (
                    'Password has been reset successfully.'
                )
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# ADMIN - USER LIST
# ============================================================

class AdminUserListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        users = User.objects.select_related('profile', 'organization').all()
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role.upper())
        search = (request.query_params.get('search') or '').strip()
        if search:
            users = users.filter(
                __import__('django.db.models', fromlist=['Q']).Q(name__icontains=search)
                | __import__('django.db.models', fromlist=['Q']).Q(email__icontains=search)
                | __import__('django.db.models', fromlist=['Q']).Q(city__icontains=search)
                | __import__('django.db.models', fromlist=['Q']).Q(country__icontains=search)
            )
        users = users.order_by('-created_at')

        return Response(
            UserSerializer(
                users,
                many=True,
                context={
                    'request': request
                }
            ).data
        )


# ============================================================
# ADMIN - USER DETAIL
# ============================================================

class AdminUserDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request, pk):

        try:
            user = User.objects.get(
                pk=pk
            )

        except User.DoesNotExist:

            return Response(
                {
                    'error': 'User not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            UserSerializer(
                user,
                context={
                    'request': request
                }
            ).data
        )

    def patch(self, request, pk):

        try:
            user = User.objects.get(
                pk=pk
            )

        except User.DoesNotExist:

            return Response(
                {
                    'error': 'User not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        allowed_fields = [
            'name',
            'phone',
            'role',
            'account_type',
            'address',
            'city',
            'country',
            'is_verified',
            'is_active',
        ]

        changed = False

        for field in allowed_fields:

            if field in request.data:

                setattr(
                    user,
                    field,
                    request.data[field]
                )

                changed = True

        if changed:
            user.save()

        return Response(
            UserSerializer(
                user,
                context={
                    'request': request
                }
            ).data
        )