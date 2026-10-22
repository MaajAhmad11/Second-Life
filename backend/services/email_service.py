import json
import urllib.error
import urllib.request

from django.conf import settings


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_platform_email(recipient_email, subject, message):
    """
    Send a Second Life transactional email through Brevo's HTTPS API.

    The Brevo API key is read only from the server environment. It is never
    exposed to the React/Vercel frontend.
    """
    recipient = (recipient_email or "").strip()

    if not recipient:
        print("Second Life email error: recipient email is empty.")
        return False

    api_key = getattr(settings, "BREVO_API_KEY", "").strip()

    if not api_key:
        print("Second Life email error: BREVO_API_KEY is not configured.")
        return False

    sender_email = (
        getattr(settings, "EMAIL_FROM_EMAIL", "")
        or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    ).strip()

    sender_name = (
        getattr(settings, "EMAIL_FROM_NAME", "")
        or "Second Life"
    ).strip()

    if not sender_email:
        print("Second Life email error: EMAIL_FROM_EMAIL is not configured.")
        return False

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": recipient,
            }
        ],
        "subject": subject,
        "textContent": message.strip(),
    }

    request = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            response_body = response.read().decode("utf-8", "replace")

        if 200 <= response.status < 300:
            print(
                f"Second Life email sent: {subject} -> {recipient}"
            )
            return True

        print(
            "Second Life email error: "
            f"Brevo returned HTTP {response.status}: {response_body}"
        )
        return False

    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", "replace")

        print(
            "Second Life email error: "
            f"Brevo HTTP {exc.code}: {response_body}"
        )
        return False

    except urllib.error.URLError as exc:
        print(
            "Second Life email error: "
            f"Brevo network error: {exc.reason}"
        )
        return False

    except Exception as exc:
        print(
            "Second Life email error: "
            f"{type(exc).__name__}: {exc}"
        )
        return False
