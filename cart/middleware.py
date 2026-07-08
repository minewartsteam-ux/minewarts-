from .cart import Cart

class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # سبد خرید را به درخواست اضافه می‌کند تا در تمام جای سایت قابل دسترس باشد
        request.cart = Cart(request)
        response = self.get_response(request)
        return response