from django.core.mail import send_mail, EmailMultiAlternatives


def sendSupportMail(subject, body, to_email):
    mail = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email="HomeBreeze Support <no-reply@homebreeze.com>",
        to=to_email,
        headers={"Reply-To": "no-reply@homebreeze.com"}
    )
    mail.send()
    pass
