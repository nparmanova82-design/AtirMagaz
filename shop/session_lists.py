"""Sessiyada saqlanadigan ro'yxatlar: sevimlilar va yaqinda ko'rilganlar.

Ro'yxatdan o'tmagan mehmonlar uchun ham ishlaydi.
"""

WISHLIST_KEY = "wishlist"
RECENT_KEY = "recently_viewed"
RECENT_LIMIT = 8


def get_wishlist(request):
    return list(request.session.get(WISHLIST_KEY, []))


def toggle_wishlist(request, perfume_id):
    """Qo'shadi yoki olib tashlaydi. Qo'shilgan bo'lsa True qaytaradi."""
    items = get_wishlist(request)
    if perfume_id in items:
        items.remove(perfume_id)
        added = False
    else:
        items.insert(0, perfume_id)
        added = True
    request.session[WISHLIST_KEY] = items
    return added


def get_recent(request):
    return list(request.session.get(RECENT_KEY, []))


def push_recent(request, perfume_id):
    items = [pk for pk in get_recent(request) if pk != perfume_id]
    items.insert(0, perfume_id)
    request.session[RECENT_KEY] = items[:RECENT_LIMIT]
