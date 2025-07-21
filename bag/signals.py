from django.contrib.auth.signals import user_logged_in
from bag.models import BagItem


@user_logged_in.connect
def merge_bag(sender, user, request, **kwargs):
    old_session_key = request.session.get('pre_login_session_key')
    if not old_session_key:
        old_session_key = request.session.session_key

    guest_items = BagItem.objects.filter(session_key=old_session_key,
                                         user__isnull=True)

    for item in guest_items:
        existing = BagItem.objects.filter(user=user,
                                          variant=item.variant).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
            item.delete()
        else:
            item.user = user
            item.session_key = None
            item.save()
