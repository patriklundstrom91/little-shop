from django.contrib import admin
from .models import Category, Product, ProductVariant, Tag, ProductTag, Review

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'slug',
        'price',
        'created',
        'updated',
        'active'
    ]
    list_filter = ['created', 'updated']
    list_editable = ['price', 'active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'size',
        'sku',
        'stock',
        'active'
    ]
    list_filter = ['stock', 'size']
    list_editable = ['stock', 'active']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'tag'
    ]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'user',
        'rating',
        'created'
    ]