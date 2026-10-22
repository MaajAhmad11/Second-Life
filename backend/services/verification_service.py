from django.utils import timezone
from django.db import transaction
from organizations.models import Organization, OrganizationVerification
from dashboard.models import ActivityLog
from services.notification_service import NotificationService

class VerificationService:
    @staticmethod
    @transaction.atomic
    def review_organization(org_id: int, admin_user, action: str, notes: str = ""):
        org = Organization.objects.select_for_update().get(id=org_id)
        action_upper = action.upper()

        if action_upper not in ['VERIFIED', 'REJECTED']:
            raise ValueError("Action must be either VERIFIED or REJECTED")

        org.verification_status = action_upper
        org.verification_reason = notes
        if action_upper == 'VERIFIED':
            org.verified_at = timezone.now()
            org.user.is_verified = True
            org.user.save(update_fields=['is_verified'])

        org.save()

        # Send approval/rejection email only after the transaction commits.
        from django.db import transaction
        from services.email_service import send_platform_email
        if action_upper == 'VERIFIED':
            email_subject = 'Your Second Life Organization Registration Is Approved'
            email_message = (
                f"Hello {org.contact_person},\\n\\n"
                f"Your organization, {org.organization_name}, has been approved on Second Life. "
                "You can now sign in and access your organization account.\\n\\n"
                "Second Life Team"
            )
        else:
            email_subject = 'Update on Your Second Life Organization Registration'
            email_message = (
                f"Hello {org.contact_person},\\n\\n"
                f"Your organization, {org.organization_name}, was not approved at this time.\\n"
                f"Reason: {notes or 'Please contact support for more information.'}\\n\\n"
                "Second Life Team"
            )
        transaction.on_commit(lambda: send_platform_email(
            org.official_email, email_subject, email_message
        ))

        # Record verification log
        OrganizationVerification.objects.create(
            organization=org,
            reviewed_by=admin_user,
            action=action_upper,
            notes=notes
        )

        # Notify Organization
        if action_upper == 'VERIFIED':
            NotificationService.send(
                user=org.user,
                title="Organization Verified! 🌟",
                message=f"Congratulations! {org.organization_name} has been verified by the SecondLife moderation team.",
                notif_type="VERIFICATION",
                link="/receiver" if org.user.role == 'RECEIVER' else "/donor"
            )
        else:
            NotificationService.send(
                user=org.user,
                title="Organization Verification Update",
                message=f"Verification was not approved: {notes}. Please update your credentials in Settings.",
                notif_type="VERIFICATION",
                link="/donor/settings" if org.user.role == 'DONOR' else "/receiver/settings"
            )

        # Activity log
        ActivityLog.objects.create(
            user=admin_user,
            action="ORGANIZATION_VERIFICATION",
            description=f"Admin {admin_user.name} set {org.organization_name} status to {action_upper}."
        )

        return org
