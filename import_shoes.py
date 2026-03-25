import os
import csv
import django

# Настройка окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoes_shop.settings')
django.setup()

from store.models import Product

def run_import():
    file_path = 'Tovar.csv'
    
    # Открываем файл и пробуем прочитать первую строку, чтобы угадать разделитель
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline()
        dialect = csv.Sniffer().sniff(first_line)
        f.seek(0) # Возвращаемся в начало файла
        
        reader = csv.DictReader(f, dialect=dialect)
        
        # Выведем список колонок, которые увидел Python (для отладки)
        print(f"Вижу колонки: {reader.fieldnames}")
        
        count = 0
        for row in reader:
            # Если артикул пустой — пропускаем строку
            if not row.get('Артикул'):
                continue
                
            try:
                # Очищаем цену
                raw_price = row['Цена'].replace(',', '.').replace('\xa0', '').strip()
                
                # Если цена пустая, ставим 0 или пропускаем
                price_value = float(raw_price) if raw_price else 0.0
                
                Product.objects.update_or_create(
                    sku=row['Артикул'],
                    defaults={
                        # ... ваши остальные поля ...
                        'price': price_value,
                        # ...
                    }
                )
                print(f"OK: {row['Артикул']}")
                count += 1
            except Exception as e:
                print(f"Пропущена строка с ошибкой: {e}")
                print(f"Доступные колонки в этой строке: {list(row.keys())}")
                break

    print(f"\nИмпорт завершен. Успешно: {count}")

if __name__ == '__main__':
    run_import()