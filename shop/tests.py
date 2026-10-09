from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Perfume, Review


class StorefrontTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_atir", verbosity=0)

    def test_all_public_pages_render(self):
        perfume = Perfume.objects.first()
        urls = [
            reverse("shop:home"), reverse("shop:catalog"), reverse("shop:brands"),
            perfume.get_absolute_url(), perfume.brand.get_absolute_url(),
            reverse("shop:wishlist"), reverse("shop:quiz"), reverse("orders:cart"), reverse("orders:track"),
            reverse("pages:about"), reverse("pages:contacts"), reverse("pages:delivery"),
            reverse("pages:faq"), reverse("pages:returns"), reverse("pages:guide"),
            reverse("accounts:login"), reverse("accounts:register"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/bunday-sahifa-yoq/").status_code, 404)

    def test_catalog_filters(self):
        r = self.client.get(reverse("shop:catalog"), {"gender": "men"})
        self.assertTrue(all(p.gender == "men" for p in r.context["page"].object_list))

        r = self.client.get(reverse("shop:catalog"), {"brand": "creed"})
        self.assertEqual({p.brand.slug for p in r.context["page"].object_list}, {"creed"})

        r = self.client.get(reverse("shop:catalog"), {"max": "500000"})
        self.assertTrue(all(p.price_from <= 500_000 for p in r.context["page"].object_list))
        self.assertGreater(r.context["total"], 0)

        r = self.client.get(reverse("shop:catalog"), {"sale": "1"})
        self.assertTrue(all(p.old_price_from for p in r.context["page"].object_list))

    def test_search_finds_by_note(self):
        r = self.client.get(reverse("shop:catalog"), {"q": "Za'faron"})
        names = {p.name for p in r.context["page"].object_list}
        self.assertIn("Baccarat Rouge 540", names)

    def test_price_sort(self):
        r = self.client.get(reverse("shop:catalog"), {"sort": "price_asc"})
        prices = [p.price_from for p in r.context["page"].object_list]
        self.assertEqual(prices, sorted(prices))

    def test_search_suggest_json(self):
        data = self.client.get(reverse("shop:search_suggest"), {"q": "sauv"}).json()
        self.assertEqual(data["results"][0]["title"], "Sauvage")

    def test_wishlist_toggle(self):
        p = Perfume.objects.first()
        url = reverse("shop:wishlist_toggle", args=[p.pk])
        r = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json(), {"added": True, "count": 1})
        r = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json(), {"added": False, "count": 0})

    def test_review_is_posted(self):
        p = Perfume.objects.first()
        before = p.reviews.count()
        r = self.client.post(p.get_absolute_url(), {"name": "Test", "rating": 4, "text": "Zo'r hid"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(p.reviews.count(), before + 1)
        self.assertEqual(Review.objects.latest("pk").rating, 4)

    def test_quiz_returns_matching_gender(self):
        r = self.client.get(reverse("shop:quiz"),
                            {"gender": "men", "family": "woody", "time": "evening", "budget": "any"})
        results = r.context["results"]
        self.assertEqual(len(results), 6)
        self.assertTrue(all(p.gender in ("men", "unisex") for p in results))
        self.assertIn(results[0].family, ("woody", "leather", "oriental"))

    def test_bottle_svg_rendered_without_image(self):
        r = self.client.get(Perfume.objects.first().get_absolute_url())
        self.assertContains(r, "<svg class=\"bottle\"", html=False)
