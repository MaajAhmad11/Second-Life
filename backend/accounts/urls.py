from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    RegisterView,
    LoginView,
    VerifyRegistrationOTPView,
    ResendRegistrationOTPView,
    MeView,
    DeleteAccountView,
    ProfileImageUploadView,
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    AdminUserListView,
    AdminUserDetailView,
)


urlpatterns = [

    # Authentication
    path(
        'auth/register/',
        RegisterView.as_view(),
        name='register'
    ),

    path(
        'auth/login/',
        LoginView.as_view(),
        name='login'
    ),

    path(
        'auth/register/verify-otp/',
        VerifyRegistrationOTPView.as_view(),
        name='verify_registration_otp'
    ),

    path(
        'auth/register/resend-otp/',
        ResendRegistrationOTPView.as_view(),
        name='resend_registration_otp'
    ),

    path(
        'auth/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    path(
        'auth/me/',
        MeView.as_view(),
        name='current_user'
    ),

    path(
        'auth/me/delete/',
        DeleteAccountView.as_view(),
        name='delete_current_account'
    ),

    path(
        'auth/profile/image/',
        ProfileImageUploadView.as_view(),
        name='profile_image_upload'
    ),

    path(
        'auth/change-password/',
        ChangePasswordView.as_view(),
        name='change_password'
    ),

    path(
        'auth/forgot-password/',
        ForgotPasswordView.as_view(),
        name='forgot_password'
    ),

    path(
        'auth/reset-password/',
        ResetPasswordView.as_view(),
        name='reset_password'
    ),

    # Admin
    path(
        'admin/users/',
        AdminUserListView.as_view(),
        name='admin_users_list'
    ),

    path(
        'admin/users/<int:pk>/',
        AdminUserDetailView.as_view(),
        name='admin_user_detail'
    ),
]