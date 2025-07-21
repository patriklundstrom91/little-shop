from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify


RATING = (
    (0, '1 Star'),
    (1, '2 Stars'),
    (2, '3 Stars'),
    (3, '4 Stars'),
    (4, '5 Stars'),
)
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'shop:product_list_by_category', args=[self.slug]
        )


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(
        upload_to='products/%y/%m/%d',
        blank=True
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            new_slug = slugify(self.name)
            count = 1
            while Product.objects.filter(slug=new_slug).exists():
                new_slug = f"{slugify(self.name)}-{count}"
                count += 1
            self.slug = new_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='variants')
    size = models.CharField(max_length=20)
    sku = models.CharField(max_length=200, unique=True)
    stock = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} - {self.size}'


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ProductTag(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200, blank=True, null=True)
    review = models.TextField(blank=True, null=True)
    rating = models.IntegerField(choices=RATING, default=4)
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'product', 'user']),
        ]
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'

    def __str__(self):
        return f'{self.product.name} - {self.user.username}'


class BackInStock(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    email = models.EmailField(max_length=200, null=False, blank=False)
    is_sent = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
