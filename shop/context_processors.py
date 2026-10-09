from django.conf import settings

from orders.cart import Cart

from .models import Perfume
from .session_lists import get_wishlist


def shop(request):
    wishlist = get_wishlist(request)
    return {
        "site": settings.SHOP,
        "cart_count": len(Cart(request)),
        "wishlist_ids": set(wishlist),
        "wishlist_count": len(wishlist),
        "nav_families": Perfume.Family.choices,
    }
