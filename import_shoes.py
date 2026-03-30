import os
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoes_shop.settings')
django.setup()

from store.models import Product, Category, Supplier

def run_import():
    file_path = 'Tovar.csv'
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        categories = {}
        suppliers = {}
        
        count = 0
        for row in reader:
            if not row.get('Артикул'):
                continue
            
            try:
                category_name = row.get('Категория товара', '').strip()
                if category_name and category_name not in categories:
                    cat, _ = Category.objects.get_or_create(name=category_name)
                    categories[category_name] = cat
                
                supplier_name = row.get('Поставщик', '').strip()
                if supplier_name and supplier_name not in suppliers:
                    sup, _ = Supplier.objects.get_or_create(name=supplier_name)
                    suppliers[supplier_name] = sup
                
                raw_price = row['Цена'].replace(',', '.').replace('\xa0', '').strip()
                price_value = float(raw_price) if raw_price else 0.0
                
                discount = int(row.get('Действующая скидка', 0) or 0)
                stock = int(row.get('Кол-во на складе', 0) or 0)
                
                Product.objects.update_or_create(
                    sku=row['Артикул'].strip(),
                    defaults={
                        'title': row.get('Наименование товара', '').strip(),
                        'unit': row.get('Единица измерения', 'шт.').strip(),
                        'price': price_value,
                        'brand': row.get('Производитель', '').strip(),
                        'category': categories.get(category_name),
                        'supplier': suppliers.get(supplier_name),
                        'discount': discount,
                        'stock': stock,
                        'description': row.get('Описание товара', '').strip(),
                        'image_name': row.get('Фото', '').strip() or None,
                    }
                )
                count += 1
            except Exception as e:
                print(f"Error: {e}")
        
        print(f"Import completed. Products: {count}")

if __name__ == '__main__':
    run_import()
