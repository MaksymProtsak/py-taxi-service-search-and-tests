from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from taxi.models import Manufacturer
from taxi_service.settings import INTERNAL_IPS
from django.core.management.commands.runserver import Command

HOME_PAGE = reverse("taxi:index")
MANUFACTURER_URL = reverse("taxi:manufacturer-list")


class PublicHomePageTest(TestCase):
    def test_login_required(self):
        res = self.client.get(HOME_PAGE)
        self.assertNotEqual(res.status_code, 200)


class PrivateHomePageTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test.user", license_number="AAA123456", password="TestPassword123"
        )
        self.client.force_login(self.user)

    def test_retrieve_manufacturers(self):
        Manufacturer.objects.create(
            name="Test Manufacturer 1",
            country="Test Country",
        )
        Manufacturer.objects.create(
            name="Test Manufacturer 2",
            country="Test Country 2",
        )
        response = self.client.get(HOME_PAGE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_manufacturers"], 2)
        self.assertEqual(response.context["num_drivers"], 1)
        self.assertEqual(response.context["num_cars"], 0)
        self.assertTemplateUsed(response, "taxi/index.html")


class PublicManufacturerTest(TestCase):
    def test_login_required(self):
        res = self.client.get(MANUFACTURER_URL)
        self.assertNotEqual(res.status_code, 200)


class PrivateManufacturerTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test.user", license_number="AAA123456", password="TestPassword123"
        )
        self.client.force_login(self.user)

    def test_retrieve_manufacturers(self):
        Manufacturer.objects.create(
            name="Test Manufacturer 1",
            country="Test Country",
        )
        Manufacturer.objects.create(
            name="Test Manufacturer 2",
            country="Test Country 2",
        )
        response = self.client.get(MANUFACTURER_URL)
        manufacturers = list(Manufacturer.objects.all())
        response_manufacturers = list(response.context["manufacturer_list"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(manufacturers, response_manufacturers)
        self.assertTemplateUsed(response, "taxi/manufacturer_list.html")

    def test_is_contain_search_form(self):
        response = self.client.get(MANUFACTURER_URL)
        self.assertIn("search_form", response.context)

    def test_search_form(self):
        test_keys = {1: "", 2: "Audi", 3: "BMW", 4: "w"}
        Manufacturer.objects.create(name="Audi", country="Germany")
        Manufacturer.objects.create(name="BMW", country="Germany")
        Manufacturer.objects.create(name="Volkswagen", country="Germany")
        manufacturers = Manufacturer.objects.all()

        response = self.client.get(MANUFACTURER_URL, {"manufacturer": test_keys[1]})
        search_value_key = response.context_data["search_form"]["manufacturer"].value()
        db_q = manufacturers.filter(name__icontains=test_keys[1])
        self.assertEqual(search_value_key, test_keys[1])
        self.assertQuerysetEqual(db_q, response.context_data["object_list"])

        for key, value in test_keys.items():
            if key != 1:
                response = self.client.get(MANUFACTURER_URL, {"manufacturer": value})
                search_value_key = response.context_data["search_form"][
                    "manufacturer"
                ].value()
                db_q = manufacturers.filter(name__icontains=value)
                self.assertNotEqual(search_value_key, test_keys[key - 1])
                self.assertEqual(search_value_key, value)
                self.assertQuerysetEqual(db_q, response.context_data["object_list"])

    def test_is_contain_paginator(self):
        res = self.client.get(MANUFACTURER_URL)
        self.assertIn("paginator", res.context)

    def test_is_pagination_appears(self):
        test_keys = {1: False, 2: False, 3: True}
        res = self.client.get(MANUFACTURER_URL)
        pagination_per_page = res.context_data["paginator"].per_page

        self.assertFalse(res.context_data["is_paginated"], test_keys[1])

        for i in range(pagination_per_page):
            Manufacturer.objects.create(
                name=f"Test manufacturer {i}", country=f"Test country {i}"
            )

        res = self.client.get(MANUFACTURER_URL)

        self.assertFalse(res.context_data["is_paginated"], test_keys[2])

        Manufacturer.objects.create(
            name=f"Test manufacturer {i + 1}", country=f"Test country {i + 1}"
        )

        res = self.client.get(MANUFACTURER_URL)

        self.assertTrue(res.context_data["is_paginated"], test_keys[3])

    def test_is_pagination_disappears(self):
        test_keys = {1: True, 2: False}
        res = self.client.get(MANUFACTURER_URL)
        pagination_per_page = res.context_data["paginator"].per_page

        for i in range(pagination_per_page + 1):
            Manufacturer.objects.create(
                name=f"Test manufacturer {i}", country=f"Test country {i}"
            )

        res = self.client.get(MANUFACTURER_URL)

        self.assertTrue(res.context_data["is_paginated"], test_keys[1])

        Manufacturer.objects.get(id=1).delete()
        res = self.client.get(MANUFACTURER_URL)

        self.assertFalse(res.context_data["is_paginated"], test_keys[2])

    def test_next_page_pagination_with_save_qwery_param(self):
        test_keys = {
            1: {},
            2: {"manufacturer": "", "page": 1},
            3: {"manufacturer": "", "page": 2},
            4: {"manufacturer": "a", "page": 1},
            5: {"manufacturer": "a", "page": 2},
            6: {"manufacturer": "T", "page": 1},
        }
        manufacturers = {
            "Toyota": "Japan",
            "BMW": "Germany",
            "Ford": "USA",
            "Hyundai": "South Korea",
            "Ferrari": "Italy",
            "Renault": "France",
            "Volvo": "Sweden",
            "Volkswagen": "Germany",
            "Kia": "South Korea",
            "Chevrolet": "USA",
            "ZAZ": "Ukraine",
        }
        res = self.client.get(MANUFACTURER_URL, test_keys[1])
        pagination_per_page = res.context_data["paginator"].per_page

        for manufacturer, country in manufacturers.items():
            Manufacturer.objects.create(name=manufacturer, country=country)

        for i in range(2, 5, 2):
            db_q = Manufacturer.objects.filter(
                name__icontains=test_keys[i]["manufacturer"]
            )
            res = self.client.get(MANUFACTURER_URL, test_keys[i])
            self.assertQuerysetEqual(
                res.context_data["manufacturer_list"], db_q[:pagination_per_page]
            )
            res = self.client.get(MANUFACTURER_URL, test_keys[i + 1])
            self.assertQuerysetEqual(
                res.context_data["manufacturer_list"],
                db_q[pagination_per_page : pagination_per_page * 2],
            )

        # db_q = Manufacturer.objects.filter(name__icontains=test_keys[6]["manufacturer"])
        # res = self.client.get(
        #     MANUFACTURER_URL,
        #     test_keys[6]
        # )
        # self.assertQuerysetEqual(
        #     res.context_data["manufacturer_list"],
        #     db_q[:pagination_per_page]
        # )

    def test_is_contain_create_button(self):
        res = self.client.get(MANUFACTURER_URL)
        self.assertContains(res, "Create")

    def test_is_create_button_has_right_url(self):
        res = self.client.get(MANUFACTURER_URL)
        self.assertContains(res, reverse("taxi:manufacturer-create"), html=False)
