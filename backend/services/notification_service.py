from notifications.models import Notification

class NotificationService:
    @staticmethod
    def send(user, title, message, notif_type=Notification.NotificationType.SYSTEM, link=""):
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=notif_type,
            link=link
        )
