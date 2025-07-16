import stripe
import json
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
import stripe.error

from orders.forms import OrderForm
from orders.models import Order, OrderItem
from shop.models import ProductVariant
from profiles.models import UserProfile
from bag.utils import get_bag_filter
from bag.models import BagItem
from django.core.mail import send_mail

# Create your views here.


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle successful stripe checkout payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    return HttpResponse(status=200)


def handle_checkout_session(session):
    metadata = session.get('metadata', {})

    bag_json = metadata.get('bag_data')
    if not bag_json:
        return
    
    bag = json.loads(bag_json)
    user_id = metadata.get('user_id')
    full_name = metadata.get('full_name')
    email = metadata.get('email')
    address = metadata.get('address')
    city = metadata.get('city')
    postal_code = metadata.get('postal_code')
    state_province = metadata.get('state_province')
    country = metadata.get('country')
    save_to_profile = metadata.get('save_to_profile') == 'true'
    grand_total = int(session.get('amount_total', 0)) / 100
    payment_intent = session.get('payment_intent')

    # Check and avoid duplicate Order creation
    if Order.objects.filter(stripe_payment_intent_id=payment_intent).exists():
        return
    subtotal = sum(item['unit_price'] * item['quantity'] for item in bag)
    if subtotal < settings.FREE_DELIVERY_THRESHOLD:
        delivery = subtotal * Decimal(
            settings.STANDARD_DELIVERY_PERCENTAGE / 100
        )
    else:
        delivery = 0

    # Create Order
    order = Order.objects.create(
        user_id=user_id or None,
        full_name=full_name,
        email=email,
        address=address,
        city=city,
        postal_code=postal_code,
        state_province=state_province,
        country=country,
        order_total=subtotal,
        delivery_cost=delivery,
        grand_total=grand_total,
        paid=True,
        stripe_payment_intent_id=payment_intent,
    )
    
    # Create OrderItems
    for item in bag:
        variant = ProductVariant.objects.get(id=item['variant_id'])
        OrderItem.objects.create(
            order=order,
            variant=variant,
            price=item['unit_price'],
            quantity=item['quantity'],
        )
    
    # Update profile
    if user_id and save_to_profile:
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        profile.full_name = full_name
        profile.email = email
        profile.address = address
        profile.city = city
        profile.postal_code = postal_code
        profile.save()

    # Send confirmation email
    send_mail(
        subject=f'Your order confirmation #{order.id}',
        message=f'Hi {full_name}, your order has been recieved. \nTotal: £{grand_total}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )


@require_POST
def create_checkout_session(request):
    data = request.POST
    save_to_profile = data.get('save_to_profile', 'true') == 'true'
    stripe.api_key = settings.STRIPE_SECRET_KEY

    bag_items = BagItem.objects.filter(**get_bag_filter(request))
    subtotal = sum(
        item.variant.product.price * item.quantity for item in bag_items
    )
    if subtotal < settings.FREE_DELIVERY_THRESHOLD:
        delivery = subtotal * Decimal(
            settings.STANDARD_DELIVERY_PERCENTAGE / 100
        )
    else:
        delivery = 0
    grand_total = subtotal + delivery

    # Serialize bag for metadata
    bag_serialized = json.dumps([
        {
            'variant_id': item.variant.id,
            'unit_price': float(item.variant.product.price),
            'quantity': item.quantity
        }
        for item in bag_items
    ])

    metadata = {
        'user_id': str(request.user.id) if request.user.is_authenticated else '',
        'bag_data': bag_serialized,
        'save_to_profile': str(save_to_profile).lower(),
        'full_name': data.get('full_name'),
        'email': data.get('email'),
        'address': data.get('address'),
        'city': data.get('city'),
        'postal_code': data.get('postal_code'),
        'state_province': data.get('state_province'),
        'country': data.get('country'),
    }

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'gbp'
                'unit_amount': int(item.variant.product.price * 100),
                'product_data': {
                    'name': item.variant.product.name,
                },
            },
            'quantity': item.quantity,
        } for item in bag_items],
        metadata=metadata,
        success_url=settings.CHECKOUT_SUCCESS_URL,
        cancel_url=settings.CHECKOUT_CANCEL_URL,
    )

    return JsonResponse({'url': session.url})
