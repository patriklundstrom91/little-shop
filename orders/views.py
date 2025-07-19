import stripe
import json
import csv
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from time import sleep

from orders.forms import OrderForm
from orders.models import Order, OrderItem
from shop.models import ProductVariant
from profiles.models import UserProfile
from bag.utils import get_bag_filter
from bag.models import BagItem
from django.core.mail import send_mail

# Create your views here.


def checkout_view(request):
    form = OrderForm(user=request.user)
    return render(request, 'orders/checkout.html', {
        'form': form,
    })


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WH_SECRET

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
    stripe_session_id = session.get('id')

    # Check and avoid duplicate Order creation
    if Order.objects.filter(stripe_payment_intent_id=payment_intent).exists():
        return
    subtotal = sum(item['unit_price'] * item['quantity'] for item in bag)
    if subtotal < settings.FREE_DELIVERY_THRESHOLD:
        delivery = Decimal(subtotal) * Decimal(
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
        stripe_checkout_session_id=stripe_session_id,
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
        delivery = Decimal(subtotal) * Decimal(
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
            'quantity': item.quantity,
            'sku': item.variant.sku,
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

    line_items = [{
        'price_data': {
            'currency': 'gbp',
            'unit_amount': int(item.variant.product.price * 100),
            'product_data': {
                'name': item.variant.product.name,
            },
        },
        'quantity': item.quantity,
    } for item in bag_items]

    if delivery > 0:
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'unit_amount': int(delivery * 100),
                'product_data': {'name': 'Delivery Charge'},
            },
            'quantity': 1,
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=line_items,
        metadata=metadata,
        success_url=settings.CHECKOUT_SUCCESS_URL,
        cancel_url=settings.CHECKOUT_CANCEL_URL,
    )

    return redirect(session.url)


def checkout_success(request):
    """ Show order success page and update product stock"""
    session_id = request.GET.get('session_id')
    session = None
    order = None
    customer_details = None
    metadata = {}
    line_items = []
    total_amount = None
    variant_ids = []
    quantities = []
    if session_id:
        for _ in range(5):
            order = Order.objects.filter(stripe_checkout_session_id=session_id).first()
            if order:
                break
            sleep(1)

    if not session_id:
        return redirect('home')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_details = session.customer_details
        metadata = session.metadata
        line_items = stripe.checkout.Session.list_line_items(session_id)
        total_amount = session.get('amount_total')
    except Exception as e:
        pass
    
    if metadata and 'bag_data' in metadata:
        try:
            bag_data = json.loads(metadata['bag_data'])
            for item in bag_data:
                variant_ids.append(item['variant_id'])
                quantities.append(item['quantity'])
        except json.JSONDecodeError:
            pass
    if variant_ids and quantities:
        for variant_id, quantity in zip(variant_ids, quantities):
            variant = get_object_or_404(ProductVariant, pk=variant_id)
            variant.stock -= quantity
            variant.save()
            
    bag_items = BagItem.objects.filter(**get_bag_filter(request))
    bag_items.delete()
    
    context = {
        'session': session,
        'customer_details': customer_details,
        'metadata': metadata,
        'line_items': line_items.data if line_items else [],
        'total_amount': total_amount,
        'order': order,
    }
    
    return render(request, 'orders/success.html', context)


def checkout_cancel(request):
    return render(request, 'orders/cancel.html')


@staff_member_required
def order_list(request):
    """ View for staff to see orders """
    delivered = request.GET.get('delivered')
    user_query = request.GET.get('user')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    orders = Order.objects.all()

    if delivered == 'true':
        orders = orders.filter(delivered=True)
    elif delivered == 'false':
        orders = orders.filter(delivered=False)

    if user_query:
        orders = orders.filter(
            Q(user__username__icontains=user_query) |
            Q(email__icontains=user_query) |
            Q(full_name__icontains=user_query)
        )

    if date_from:
        orders = orders.filter(created__date__gte=date_from)
    if date_to:
        orders = orders.filter(created__date__lte=date_to)
    context = {
        'orders': orders,
        'filter_value': delivered,
        'user_query': user_query,
        'date_from': date_from,
        'date_to': date_to
    }
    return render(request, 'orders/order_list.html', context)


@staff_member_required
def order_detail(request, pk):
    """ View for order details """
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})


@staff_member_required
def export_orders_csv(request):
    """ Export to CSV view """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Created Date', 'Delivered', 'Total'])

    orders = Order.objects.all()

    for order in orders:
        writer.writerow([
            order.id,
            order.full_name,
            order.email,
            order.created.strftime("%Y-%m-%d %H:%M"),
            "Yes" if order.delivered else "No",
            str(order.grand_total),
        ])

    return response
