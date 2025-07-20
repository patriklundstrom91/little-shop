from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import BackInStock


def notify_back_in_stock(variant):
    """ Sends back in stock email when stock is added """
    notifications = BackInStock.objects.filter(variant=variant,
                                               is_sent=False)

    subject = f'Good news: "{variant.product.name}" is back in stock!'

    for note in notifications:
        message = render_to_string('shop/emails/back_in_stock.txt', {
            'variant': variant,
        })

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[note.email],
            fail_silently=False,
        )

        note.is_sent = True
        note.save()
