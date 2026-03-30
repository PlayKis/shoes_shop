from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Order, OrderItem, UserProfile, Category, Supplier, PickupPoint


def get_user_role(user):
    if not user.is_authenticated:
        return 'guest'
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return 'client'


def product_list(request):
    products = Product.objects.all()
    role = get_user_role(request.user)

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '')

    if search_query and role in ['manager', 'admin']:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )

    if category_filter:
        products = products.filter(category_id=category_filter)

    if sort_by == 'asc':
        products = products.order_by('stock')
    elif sort_by == 'desc':
        products = products.order_by('-stock')

    categories = Category.objects.all()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())

    user_full_name = ''
    if request.user.is_authenticated:
        try:
            user_full_name = request.user.profile.get_full_name()
        except UserProfile.DoesNotExist:
            user_full_name = request.user.get_full_name() or request.user.username

    return render(request, 'store/list.html', {
        'products': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'cart_count': cart_count,
        'user_role': role,
        'user_full_name': user_full_name,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'categories': categories,
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('product_list')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('product_list')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        UserProfile.objects.create(user=user, role='client')
        login(request, user)
        return redirect('product_list')

    return render(request, 'store/register.html')


@login_required
def product_create(request):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для добавления товаров')
        return redirect('product_list')

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            supplier_id = request.POST.get('supplier')
            sku = request.POST.get('sku')
            
            if Product.objects.filter(sku=sku).exists():
                messages.error(request, 'Товар с таким артикулом уже существует')
                return redirect('product_create')

            product = Product(
                sku=sku,
                title=request.POST.get('title'),
                brand=request.POST.get('brand'),
                category_id=category_id if category_id else None,
                supplier_id=supplier_id if supplier_id else None,
                price=request.POST.get('price'),
                unit=request.POST.get('unit', 'шт.'),
                stock=request.POST.get('stock', 0),
                description=request.POST.get('description', ''),
                discount=request.POST.get('discount', 0),
            )
            
            image = request.FILES.get('image')
            if image:
                import os
                from django.conf import settings
                filename = f"{sku}_{image.name}"
                filepath = os.path.join(settings.BASE_DIR, 'static', 'images', filename)
                with open(filepath, 'wb+') as dest:
                    for chunk in image.chunks():
                        dest.write(chunk)
                product.image_name = filename

            product.save()
            messages.success(request, 'Товар успешно добавлен')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')

    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'store/product_form.html', {
        'categories': categories,
        'suppliers': suppliers,
        'product': None
    })


@login_required
def product_edit(request, pk):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для редактирования товаров')
        return redirect('product_list')

    product = get_object_or_404(Product, pk=pk)
    old_image = product.image_name

    if request.method == 'POST':
        try:
            product.title = request.POST.get('title')
            product.brand = request.POST.get('brand')
            product.category_id = request.POST.get('category') or None
            product.supplier_id = request.POST.get('supplier') or None
            product.price = request.POST.get('price')
            product.unit = request.POST.get('unit', 'шт.')
            product.stock = request.POST.get('stock', 0)
            product.description = request.POST.get('description', '')
            product.discount = request.POST.get('discount', 0)

            image = request.FILES.get('image')
            if image:
                import os
                from django.conf import settings
                if old_image:
                    old_filepath = os.path.join(settings.BASE_DIR, 'static', 'images', old_image)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                filename = f"{product.sku}_{image.name}"
                filepath = os.path.join(settings.BASE_DIR, 'static', 'images', filename)
                with open(filepath, 'wb+') as dest:
                    for chunk in image.chunks():
                        dest.write(chunk)
                product.image_name = filename

            product.save()
            messages.success(request, 'Товар успешно обновлен')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Ошибка при редактировании товара: {str(e)}')

    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'store/product_form.html', {
        'categories': categories,
        'suppliers': suppliers,
        'product': product
    })


@login_required
def product_delete(request, pk):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для удаления товаров')
        return redirect('product_list')

    product = get_object_or_404(Product, pk=pk)

    if Order.objects.filter(product=product).exists():
        messages.error(request, 'Нельзя удалить товар, который присутствует в заказе')
        return redirect('product_list')

    if request.method == 'POST':
        import os
        from django.conf import settings
        if product.image_name:
            filepath = os.path.join(settings.BASE_DIR, 'static', 'images', product.image_name)
            if os.path.exists(filepath):
                os.remove(filepath)
        product.delete()
        messages.success(request, 'Товар успешно удален')
        return redirect('product_list')

    return render(request, 'store/product_confirm_delete.html', {'product': product})


@login_required
def order_list(request):
    role = get_user_role(request.user)
    if role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к заказам')
        return redirect('product_list')

    orders = Order.objects.select_related('product', 'customer').all()
    return render(request, 'store/order_list.html', {
        'orders': orders,
        'user_role': role,
        'user_full_name': request.user.profile.get_full_name() if hasattr(request.user, 'profile') else str(request.user)
    })


@login_required
def order_create(request):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для создания заказов')
        return redirect('order_list')

    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, pk=request.POST.get('product'))
            customer_id = request.POST.get('customer')
            customer = User.objects.get(pk=customer_id) if customer_id else None

            order = Order(
                article=request.POST.get('article') or None,
                status=request.POST.get('status', 'pending'),
                pickup_address=request.POST.get('pickup_address'),
                issue_date=request.POST.get('issue_date') or None,
                customer=customer
            )
            order.save()
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=request.POST.get('quantity', 1)
            )
            
            messages.success(request, 'Заказ успешно создан')
            return redirect('order_list')
        except Exception as e:
            messages.error(request, f'Ошибка при создании заказа: {str(e)}')

    products = Product.objects.all()
    customers = User.objects.all()
    return render(request, 'store/order_form.html', {
        'products': products,
        'customers': customers,
        'order': None
    })


@login_required
def order_edit(request, pk):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для редактирования заказов')
        return redirect('order_list')

    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        try:
            order.article = request.POST.get('article') or None
            order.status = request.POST.get('status', 'pending')
            order.pickup_address = request.POST.get('pickup_address')
            customer_id = request.POST.get('customer')
            order.customer = User.objects.get(pk=customer_id) if customer_id else None
            order.issue_date = request.POST.get('issue_date') or None
            order.save()
            
            item_product_id = request.POST.get('product')
            item_quantity = request.POST.get('quantity', 1)
            if item_product_id:
                order.items.all().delete()
                OrderItem.objects.create(
                    order=order,
                    product_id=item_product_id,
                    quantity=item_quantity
                )
            
            messages.success(request, 'Заказ успешно обновлен')
            return redirect('order_list')
        except Exception as e:
            messages.error(request, f'Ошибка при редактировании заказа: {str(e)}')

    products = Product.objects.all()
    customers = User.objects.all()
    return render(request, 'store/order_form.html', {
        'products': products,
        'customers': customers,
        'order': order
    })


@login_required
def order_delete(request, pk):
    if get_user_role(request.user) != 'admin':
        messages.error(request, 'У вас нет прав для удаления заказов')
        return redirect('order_list')

    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Заказ успешно удален')
        return redirect('order_list')

    return render(request, 'store/order_confirm_delete.html', {'order': order})


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    p_id = str(product_id)
    cart[p_id] = cart.get(p_id, 0) + 1
    request.session['cart'] = cart
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('product_list')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    p_id = str(product_id)
    if p_id in cart:
        del cart[p_id]
        request.session['cart'] = cart
    return redirect('cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            item_total = float(product.final_price) * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
            total_price += item_total
        except Product.DoesNotExist:
            pass

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'pickup_points': PickupPoint.objects.all()
    })


def create_order(request):
    if request.method == 'POST':
        pickup_point_id = request.POST.get('pickup_point')
        pickup_point = get_object_or_404(PickupPoint, pk=pickup_point_id)
        
        cart = request.session.get('cart', {})
        customer = request.user if request.user.is_authenticated else None
        
        if not cart:
            messages.error(request, 'Корзина пуста')
            return redirect('cart_detail')
        
        order = Order.objects.create(
            pickup_address=pickup_point.address,
            customer=customer
        )
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(pk=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )
            except Product.DoesNotExist:
                pass
        
        request.session['cart'] = {}
        messages.success(request, 'Заказ успешно оформлен!')
        return redirect('product_list')
    
    return redirect('cart_detail')


def order_history(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Войдите для просмотра истории заказов')
        return redirect('login')
    
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')
    return render(request, 'store/order_history.html', {'orders': orders})