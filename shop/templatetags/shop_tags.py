import itertools

from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()

_ids = itertools.count(1)

CAPS = {
    "gold": ("#F3E3B5", "#C9A45C", "#8A6A32"),
    "black": ("#5A5A5A", "#232323", "#0B0B0B"),
    "silver": ("#FAFAFA", "#C3C7CC", "#878C93"),
}


@register.filter
def som(value):
    """1250000 → «1 250 000 so'm» (bo'linmaydigan bo'shliqlar bilan)."""
    if value in (None, ""):
        return ""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f"{value:,}".replace(",", " ") + " so'm"


@register.filter
def num(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value


@register.filter
def get_item(mapping, key):
    return mapping.get(key) if mapping else None


@register.simple_tag
def url_replace(request, field, value):
    """Joriy GET parametrlarini saqlab, bittasini almashtiradi (sahifalash, saralash)."""
    params = request.GET.copy()
    params[field] = value
    if field != "page":
        params.pop("page", None)
    return params.urlencode()


@register.simple_tag
def url_without(request, field, value=None):
    """Faol filtr «chip»ini olib tashlash uchun havola."""
    params = request.GET.copy()
    if value is None:
        params.pop(field, None)
    else:
        values = [v for v in params.getlist(field) if v != str(value)]
        params.setlist(field, values)
    params.pop("page", None)
    return params.urlencode()


@register.inclusion_tag("includes/stars.html")
def stars(rating, size="sm"):
    rating = float(rating or 0)
    return {"rating": rating, "pct": round(rating / 5 * 100, 1), "size": size}


def _rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (217, 164, 65)


def _mix(hex_color, target, t):
    r, g, b = _rgb(hex_color)
    tr, tg, tb = target
    return "#{:02x}{:02x}{:02x}".format(
        round(r + (tr - r) * t), round(g + (tg - g) * t), round(b + (tb - b) * t))


def _luma(hex_color):
    r, g, b = _rgb(hex_color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _inset_polygon(points, k):
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in points]


def _pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


# Har bir shakl: qopqoq (x, y, w, h, rx), bo'yin (x, y, w, h), tana (svg-shakl funksiyasi), yorliq markazi
def _shape(shape):
    if shape == "round":
        return {
            "cap": (78, 34, 44, 52, 8), "neck": (88, 84, 24, 22),
            "outer": lambda f: f'<circle cx="100" cy="186" r="80" fill="{f}"/>',
            "inner": lambda f: f'<circle cx="100" cy="186" r="72" fill="{f}"/>',
            "label": (100, 196), "label_w": 86, "hl": (44, 150, 10, 70), "floor": 266,
        }
    if shape == "tall":
        return {
            "cap": (80, 14, 40, 58, 5), "neck": (88, 70, 24, 18),
            "outer": lambda f: f'<rect x="56" y="86" width="88" height="178" rx="16" fill="{f}"/>',
            "inner": lambda f: f'<rect x="63" y="94" width="74" height="163" rx="11" fill="{f}"/>',
            "label": (100, 190), "label_w": 64, "hl": (68, 104, 8, 140), "floor": 266,
        }
    if shape == "square":
        return {
            "cap": (68, 30, 64, 56, 4), "neck": (88, 84, 24, 16),
            "outer": lambda f: f'<rect x="28" y="98" width="144" height="166" rx="18" fill="{f}"/>',
            "inner": lambda f: f'<rect x="42" y="112" width="116" height="138" rx="8" fill="{f}"/>',
            "label": (100, 184), "label_w": 92, "hl": (48, 120, 8, 120), "floor": 266,
        }
    if shape == "facet":
        outer = [(62, 98), (138, 98), (170, 132), (170, 230), (138, 264), (62, 264), (30, 230), (30, 132)]
        inner = _inset_polygon(outer, 0.9)
        return {
            "cap": (74, 30, 52, 56, 3), "neck": (88, 84, 24, 16),
            "outer": lambda f: f'<polygon points="{_pts(outer)}" fill="{f}"/>',
            "inner": lambda f: f'<polygon points="{_pts(inner)}" fill="{f}"/>',
            "facets": f'<polyline points="62,98 76,124 124,124 138,98" fill="none"/>'
                      f'<polyline points="62,264 76,238 124,238 138,264" fill="none"/>'
                      f'<line x1="76" y1="124" x2="76" y2="238"/><line x1="124" y1="124" x2="124" y2="238"/>'
                      f'<line x1="30" y1="132" x2="76" y2="124"/><line x1="170" y1="132" x2="124" y2="124"/>'
                      f'<line x1="30" y1="230" x2="76" y2="238"/><line x1="170" y1="230" x2="124" y2="238"/>',
            "label": (100, 184), "label_w": 58, "hl": (40, 140, 7, 86), "floor": 266,
        }
    # classic
    return {
        "cap": (72, 26, 56, 58, 5), "neck": (86, 82, 28, 18),
        "outer": lambda f: f'<rect x="38" y="98" width="124" height="166" rx="12" fill="{f}"/>',
        "inner": lambda f: f'<rect x="46" y="106" width="108" height="150" rx="7" fill="{f}"/>',
        "label": (100, 184), "label_w": 80, "hl": (54, 116, 8, 128), "floor": 266,
    }


@register.simple_tag
def bottle(perfume, css_class="bottle"):
    """Atir flakonini SVG ko'rinishida chizadi (rasm yuklanmagan bo'lsa)."""
    if getattr(perfume, "image", None):
        return format_html('<img class="{}" src="{}" alt="{}" loading="lazy">',
                           css_class, perfume.image.url, str(perfume))

    uid = f"b{next(_ids)}"
    color = perfume.color or "#D9A441"
    s = _shape(perfume.shape)
    cap_hi, cap_mid, cap_lo = CAPS.get(perfume.cap, CAPS["gold"])
    liquid_top = _mix(color, (255, 255, 255), 0.28)
    liquid_bottom = _mix(color, (0, 0, 0), 0.22)
    glass = _mix(color, (255, 255, 255), 0.72)
    dark_liquid = _luma(color) < 110
    label_fill = "#FFFFFF" if not dark_liquid else "#F5EFE6"
    ink = "#1d1a17"

    brand = perfume.brand.name.upper()
    # Uzun brend nomlari yorliqqa sig'ishi uchun shrift kichrayadi, kerak bo'lsa siqiladi
    fs = max(6.5, min(11.5, s["label_w"] * 1.1 / max(len(brand), 1)))
    fit_w = s["label_w"] * 0.86
    fit = f' textLength="{fit_w:.1f}" lengthAdjust="spacingAndGlyphs"' if len(brand) * (fs * 0.62 + 1.2) > fit_w else ""
    conc = perfume.get_concentration_display().upper()
    lx, ly = s["label"]
    lw = s["label_w"]
    cx, cy, cw, ch, crx = s["cap"]
    nx, ny, nw, nh = s["neck"]
    hx, hy, hw, hh = s["hl"]

    svg = f"""
<svg class="{escape(css_class)}" viewBox="0 0 200 280" role="img" aria-label="{escape(str(perfume))}">
  <defs>
    <linearGradient id="{uid}l" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{liquid_top}"/><stop offset="1" stop-color="{liquid_bottom}"/>
    </linearGradient>
    <linearGradient id="{uid}g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".55"/>
      <stop offset=".5" stop-color="{glass}" stop-opacity=".35"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity=".6"/>
    </linearGradient>
    <linearGradient id="{uid}c" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{cap_lo}"/><stop offset=".35" stop-color="{cap_hi}"/>
      <stop offset=".7" stop-color="{cap_mid}"/><stop offset="1" stop-color="{cap_lo}"/>
    </linearGradient>
    <radialGradient id="{uid}s" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#000" stop-opacity=".22"/><stop offset="1" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <ellipse cx="100" cy="{s['floor']}" rx="86" ry="9" fill="url(#{uid}s)"/>
  {s['outer'](f'url(#{uid}g)')}
  {s['inner'](f'url(#{uid}l)')}
  {s['outer']('none').replace('fill="none"', 'fill="none" stroke="#ffffff" stroke-opacity=".7" stroke-width="1.5"')}
  <g stroke="#ffffff" stroke-opacity=".28" stroke-width="1">{s.get('facets', '')}</g>
  <rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="{hw / 2}" fill="#fff" opacity=".45"/>
  <rect x="{hx + hw + 5}" y="{hy + 6}" width="{hw / 2.5:.1f}" height="{hh * 0.55:.1f}" rx="2" fill="#fff" opacity=".25"/>
  <rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" fill="url(#{uid}c)" opacity=".9"/>
  <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="{crx}" fill="url(#{uid}c)"/>
  <rect x="{cx + 5}" y="{cy + 4}" width="{cw - 10}" height="3" rx="1.5" fill="#fff" opacity=".35"/>
  <g>
    <rect x="{lx - lw / 2}" y="{ly - 17}" width="{lw}" height="34" rx="2" fill="{label_fill}" opacity=".92"/>
    <text x="{lx}" y="{ly - 1}" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif"
          font-size="{fs:.1f}" font-weight="600" letter-spacing="1.2" fill="{ink}"{fit}>{escape(brand)}</text>
    <line x1="{lx - 10}" y1="{ly + 4}" x2="{lx + 10}" y2="{ly + 4}" stroke="{cap_mid}" stroke-width=".8"/>
    <text x="{lx}" y="{ly + 11}" text-anchor="middle" font-family="Manrope, Arial, sans-serif"
          font-size="4.2" letter-spacing="1" fill="#6b625a">{escape(conc)}</text>
  </g>
</svg>"""
    return mark_safe(svg)
