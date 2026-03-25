from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Указываем только те поля, которые реально есть в models.py
    list_display = ('sku', 'title', 'brand', 'price', 'discount', 'stock')
    
    # Поля, которые можно редактировать прямо в списке (не заходя в карточку)
    # Убираем 'available', заменяем на 'stock' или 'price'
    list_editable = ('price', 'discount', 'stock')
    
    # Поля, по которым будет работать поиск
    search_fields = ('sku', 'title', 'brand')
    
    # Фильтры справа
    list_filter = ('brand', 'category')