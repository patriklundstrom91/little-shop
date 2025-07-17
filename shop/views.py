from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Category, Product, ProductVariant, Tag, ProductTag, Review
from bag.forms import AddToBagForm
from bag.models import BagItem
from bag.utils import get_bag_filter

# Create your views here.


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(active=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(
        request,
        'shop/product/list.html',
        {
            'category': category,
            'categories': categories,
            'products': products,
        }
    )


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product, id=id, slug=slug, active=True
    )
    variants = product.variants.filter(active=True)
    
    # Handle GET variant
    selected_variant = None
    variant_id = request.GET.get('variant')
    if variant_id:
        selected_variant = get_object_or_404(ProductVariant,
                                             pk=variant_id, product=product)
    # Handle POST add to bag    
    form = AddToBagForm(product=product, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        variant = form.cleaned_data['variant']
        quantity = form.cleaned_data['quantity']
        selected_variant = variant
        if not request.session.session_key:
            request.session.create()
        bag_filter = get_bag_filter(request)
        bag_item, created = BagItem.objects.get_or_create(
            variant=variant,
            defaults={'quantity': quantity},
            **bag_filter
        )
        if not created:
            bag_item.quantity += quantity
            bag_item.save()
        messages.success(
            request,
            f'{variant.product.name} ({variant.size}) added to your bag.'
        )
        return redirect('bag:view_bag')
    
    # Handle reviews and rating
    reviews = Review.objects.filter(product=product.id, published=True)
    review_count = reviews.count()
    if review_count:
        avg_rating = sum([r.rating + 1 for r in reviews]) / review_count
    else:
        avg_rating = None
    review_summary = {
        '5': reviews.filter(rating=4).count(),
        '4': reviews.filter(rating=3).count(),
        '3': reviews.filter(rating=2).count(),
        '2': reviews.filter(rating=1).count(),
        '1': reviews.filter(rating=0).count(),
    }

    return render(
        request,
        'shop/product/detail.html',
        {'product': product,
         'variants': variants,
         'selected_variant': selected_variant,
         'reviews': reviews,
         'review_count': review_count,
         'avg_rating': avg_rating,
         'review_summary': review_summary,
         'form': form,
         }
    )