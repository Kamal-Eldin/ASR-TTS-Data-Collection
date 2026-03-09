import boto3
from botocore.exceptions import ClientError
from config import AppConfig


class EmailService:
    """Send emails via AWS SES"""

    @staticmethod
    def _get_ses_client():
        access_id = AppConfig.get_aws_access_id()
        access_secret = AppConfig.get_aws_access_secret()

        kwargs = {"region_name": AppConfig.AWS_DEFAULT_REGION}
        if access_id and access_secret:
            kwargs["aws_access_key_id"] = access_id
            kwargs["aws_secret_access_key"] = access_secret

        return boto3.client("ses", **kwargs)

    @classmethod
    def send_password_reset_email(cls, to_email: str, reset_token: str) -> bool:
        """Send a password reset link via SES. Returns True on success."""
        sender = AppConfig.SES_SENDER_EMAIL
        if not sender:
            print("[EmailService] SES_SENDER_EMAIL not configured, skipping email")
            return False

        reset_link = f"{AppConfig.FRONTEND_URL}/reset-password?token={reset_token}"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
            <h2 style="color: #0A0A0A; text-align: center;">Password Reset</h2>
            <p style="color: #555; font-size: 15px; line-height: 1.6;">
                You requested a password reset. Click the button below to set a new password.
                This link expires in 15 minutes.
            </p>
            <div style="text-align: center; margin: 28px 0;">
                <a href="{reset_link}"
                   style="background: #030213; color: #fff; padding: 12px 32px;
                          border-radius: 8px; text-decoration: none; font-size: 14px;">
                    Reset Password
                </a>
            </div>
            <p style="color: #999; font-size: 13px;">
                If you didn't request this, you can safely ignore this email.
            </p>
        </div>
        """

        text_body = (
            f"You requested a password reset.\n\n"
            f"Click here to reset your password: {reset_link}\n\n"
            f"This link expires in 15 minutes.\n"
            f"If you didn't request this, ignore this email."
        )

        try:
            client = cls._get_ses_client()
            client.send_email(
                Source=sender,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Password Reset Request", "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
            print(f"[EmailService] Reset email sent to {to_email}")
            return True
        except ClientError as e:
            print(f"[EmailService] SES error: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"[EmailService] Failed to send email: {e}")
            return False
