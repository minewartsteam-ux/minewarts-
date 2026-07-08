from decimal import Decimal
from django.conf import settings

# این خط را اضافه کردیم تا خطا برطرف شود
from shop.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False, month_option=None):
        product_id = str(product.id)
        
        # استفاده از قیمت وارت کوین
        # فقط برای محصولاتی که نوع آن‌ها رنک است و گزینه ماهانه دارند، از گزینه ماهانه استفاده کن
        if (
            month_option is not None
            and getattr(product, 'product_type', None) == getattr(Product, 'PRODUCT_TYPE_RANK', 'rank')
            and getattr(product, 'has_monthly_options', False)
        ):
            # ایجاد کلید منحصر به فرد برای محصول + گزینه ماهانه
            cart_key = f"{product_id}_{month_option.id}"
            wart_coin_price = month_option.get_wart_coin_price()
            months = month_option.months
        else:
            cart_key = product_id
            wart_coin_price = product.wart_coin_price
            months = None
        
        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'quantity': 0, 
                'wart_coin_price': str(wart_coin_price),
                'product_id': product_id,
                'month_option_id': str(month_option.id) if month_option is not None else None,
                'months': months
            }
        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product, month_option_id=None):
        # حذف بر اساس product_id و month_option_id
        keys_to_remove = []
        product_id_str = str(product.id)
        
        for key in self.cart.keys():
            item = self.cart[key]
            if item.get('product_id') == product_id_str:
                if month_option_id is None or item.get('month_option_id') == str(month_option_id):
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cart[key]
        self.save()

    def __iter__(self):
        cart = self.cart.copy()
        if not cart:
            return
        
        # جمع‌آوری product_id ها و month_option_id ها
        product_ids = set()
        month_option_ids = set()
        
        for key, item in cart.items():
            if 'product_id' in item:
                try:
                    product_ids.add(int(item['product_id']))
                    if item.get('month_option_id'):
                        month_option_ids.add(int(item['month_option_id']))
                except (ValueError, TypeError):
                    continue
        
        if not product_ids:
            return
        
        # بارگذاری محصولات و گزینه‌های ماهانه
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        month_options = {}
        if month_option_ids:
            from shop.models import ProductMonth
            month_options = {mo.id: mo for mo in ProductMonth.objects.filter(id__in=month_option_ids)}
        
        # اضافه کردن محصول و گزینه ماهانه به هر آیتم
        for key, item in cart.items():
            if 'product_id' in item:
                try:
                    product_id = int(item['product_id'])
                    if product_id in products:
                        # ایجاد یک کپی از item برای جلوگیری از تغییر session
                        item_copy = item.copy()
                        item_copy['product'] = products[product_id]
                        
                        # اگر گزینه ماهانه دارد، آن را اضافه کن
                        if item.get('month_option_id'):
                            month_option_id = int(item['month_option_id'])
                            if month_option_id in month_options:
                                item_copy['month_option'] = month_options[month_option_id]
                        
                        # استفاده از قیمت وارت کوین - تبدیل به Decimal فقط در کپی
                        wart_coin_price = Decimal(item.get('wart_coin_price', '0'))
                        item_copy['wart_coin_price'] = wart_coin_price
                        item_copy['total_wart_coin_price'] = wart_coin_price * item['quantity']
                        # برای سازگاری با کد قدیمی
                        item_copy['price'] = wart_coin_price
                        item_copy['total_price'] = item_copy['total_wart_coin_price']
                        yield item_copy
                except (ValueError, TypeError, KeyError):
                    continue

    def __len__(self):
        return sum(item.get('quantity', 0) for item in self.cart.values() if isinstance(item, dict))

    def get_total_price(self):
        """قیمت کل به وارت کوین"""
        total = Decimal('0')
        for item in self.cart.values():
            if isinstance(item, dict) and 'wart_coin_price' in item and 'quantity' in item:
                try:
                    total += Decimal(item['wart_coin_price']) * item['quantity']
                except (ValueError, TypeError):
                    continue
        return total
    
    def get_total_wart_coin_price(self):
        """نام مستعار برای سازگاری"""
        return self.get_total_price()

    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.session.modified = True