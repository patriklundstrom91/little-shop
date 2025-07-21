from django.shortcuts import render, get_object_or_404, redirect
from bag.contexts import bag_contents
from django.contrib import messages
from shop.models import ProductVariant
from .utils import get_bag_filter
from .models import BagItem

# Create your views here.


def view_bag(request):
    """ A view to render the bag content """
    context = bag_contents(request)
    return render(request, 'bag/bag.html', context)


def update_bag_item(request):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        if not variant_id:
            messages.error(request, "No product selected for update.")
            return redirect('bag:view_bag')
        new_qty = int(request.POST.get('quantity', 1))

        variant = get_object_or_404(ProductVariant, pk=variant_id)

        max_qty = variant.stock
        quantity = min(new_qty, max_qty)

        bag_filter = get_bag_filter(request)
        bag_item = BagItem.objects.filter(variant=variant,
                                          **bag_filter).first()

        if bag_item:
            if quantity > 0:
                bag_item.quantity = quantity
                bag_item.save()
                messages.success(
                    request,
                    f'Updated quantity to {quantity} for {variant}'
                )
            else:
                bag_item.delete()
                messages.success(
                    request,
                    f'Removed {variant} from your bag'
                )
        else:
            messages.error(request, 'Item not found in your bag')

    return redirect('bag:view_bag')
