from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('client', 'Клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username


class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование поставщика")
    contact = models.CharField(max_length=255, verbose_name="Контактные данные")
    address = models.TextField(blank=True, verbose_name="Адрес")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категория товара")

    def __str__(self):
        return self.name


class PickupPoint(models.Model):
    address = models.CharField(max_length=255, unique=True, verbose_name="Адрес пункта выдачи")

    def __str__(self):
        return self.address


class Product(models.Model):
    UNIT_CHOICES = [
        ('шт.', 'шт.'),
        ('пара', 'пара'),
        ('кг', 'кг'),
    ]
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    title = models.CharField(max_length=255, verbose_name="Наименование товара")
    brand = models.CharField(max_length=100, verbose_name="Производитель")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория товара")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Поставщик")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='шт.', verbose_name="Единица измерения")
    stock = models.IntegerField(default=0, verbose_name="Кол-во на складе")
    description = models.TextField(blank=True, null=True, verbose_name="Описание товара")
    discount = models.IntegerField(default=0, verbose_name="Действующая скидка")
    image_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фото")

    @property
    def final_price(self):
        if self.discount > 0:
            return round(float(self.price) * (1 - self.discount / 100), 2)
        return float(self.price)

    @property
    def get_image_url(self):
        if self.image_name:
            return f"/static/images/{self.image_name}"
        return "/static/images/picture.png"

    @property
    def category_name(self):
        return self.category.name if self.category else ""

    @property
    def supplier_name(self):
        return self.supplier.name if self.supplier else ""


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'В обработке'),
        ('ready', 'Готов к выдаче'),
        ('completed', 'Выдан'),
        ('cancelled', 'Отменен'),
    ]
    article = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Артикул")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус заказа")
    pickup_address = models.CharField(max_length=255, verbose_name="Адрес пункта выдачи")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    issue_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата выдачи")
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    @property
    def total_price(self):
        return sum(float(item.product.final_price) * item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.IntegerField(default=1, verbose_name="Количество")

    @property
    def item_total(self):
        return float(self.product.final_price) * self.quantity