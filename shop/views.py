from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Category, Product, ProductVariant, Tag, ProductTag, Review, BackInStock
from .forms import ProductForm, ProductVariantFormSet, ReviewForm
from bag.forms import AddToBagForm
from bag.models import BagItem
from bag.utils import get_bag_filter
from django.utils.timezone import now

# Create your views here.


def product_list(request, category_slug=None):
    """ Product list view to show all products"""
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


def product_search(request):
    """ Product search """
    query = request.GET.get('search', '')
    products = Product.objects.filter(
        name__icontains=query, active=True
    ) if query else Product.objects.none()

    context = {
        'products': products,
        'query': query,
        'category': None,
        'categories': Category.objects.all(),
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, id, slug):
    """ Product detail, add to bag and product rating/review view"""
    product = get_object_or_404(
        Product, id=id, slug=slug, active=True
    )
    variants = product.variants.filter(active=True)
    selected_variant = None
    variant_id = request.GET.get('variant')
    if variant_id:
        selected_variant = get_object_or_404(ProductVariant,
                                             pk=variant_id, product=product)
        
    form = AddToBagForm(product=product, data=request.POST or None)
    review_form = ReviewForm()
    if request.method == 'POST' and 'submit_review' in request.POST and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.published = True
            review.save()
            messages.success(request, "Your review was submitted.")
            return redirect('shop:product_detail', id=product.id, slug=product.slug)
        
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
    
    reviews = Review.objects.filter(product=product.id, published=True)
    user_reviews = reviews.filter(user=request.user) if request.user.is_authenticated else None
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
    context = {
        'product': product,
        'variants': variants,
        'selected_variant': selected_variant,
        'reviews': reviews,
        'review_count': review_count,
        'review_form': review_form,
        'user_reviews': user_reviews,
        'avg_rating': avg_rating,
        'review_summary': review_summary,
        'form': form,
    }
    return render(request, 'shop/product/detail.html', context)


@staff_member_required
def add_product(request):
    """ View to allow logged in staff to add products front-end """
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            product = product_form.save(commit=False)
            formset = ProductVariantFormSet(request.POST, instance=product)
            if formset.is_valid():
                product.save()
                formset.save()
                return redirect('shop:product_list')
        else:
            formset = ProductVariantFormSet(request.POST)
    else:
        product_form = ProductForm()
        formset = ProductVariantFormSet()

    return render(request, 'shop/product/add_product.html', {
        'product_form': product_form,
        'variant_formset': formset,
    })


@staff_member_required
def edit_product(request, pk):
    """ View to allow staff to edit/delete products front-end """
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES,
                                   instance=product)
        formset = ProductVariantFormSet(request.POST, instance=product)
        if product_form.is_valid() and formset.is_valid():
            product = product_form.save()
            formset.save()
            return redirect('shop:product_detail', id=product.id,
                            slug=product.slug)
    else:
        product_form = ProductForm(instance=product)
        formset = ProductVariantFormSet(instance=product)

    return render(request, 'shop/product/edit_product.html', {
        'product_form': product_form,
        'variant_formset': formset,
        'product': product,
    })


@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('shop:product_list')
    return render(
        request, 'shop/product/confirm_delete.html', {'product': product}
    )


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Review updated.')
        return redirect('shop:product_detail', id=review.product.id,
                        slug=review.product.slug)
    return render(
        request, 'shop/reviews/edit_review.html', {
            'form': form, 'review': review
        }
    )


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review removed.')
        return redirect('shop:product_detail', id=review.product.id,
                        slug=review.product.slug)
    return render(request, 'shop/reviews/delete_review.html', {
        'review': review
    })


def back_in_stock(request, variant_id):
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        existing = BackInStock.objects.filter(variant=variant, email=email, is_sent=False)
        if existing.exists():
            messages.info(request,
                          'You have already signed up for a restock notification for this product')
        else:
            BackInStock.objects.create(variant=variant, email=email)
            messages.success(request,
                             'You will be notified when back in stock!')
        return redirect('shop:product_detail', id=variant.product.id,
                        slug=variant.product.slug)
    return redirect('shop:product_detail', id=variant.product.id,
                    slug=variant.product.slug)
