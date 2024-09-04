from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from taxi.models import Manufacturer

HOME_PAGE = reverse("taxi:index")
MANUFACTURER_URL = reverse("taxi:manufacturer-list")


class PublicHomePageTest(TestCase):
    def test_login_required(self):
        res = self.client.get(HOME_PAGE)
        self.assertNotEqual(res.status_code, 200)


class PrivateHomePageTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test.user",
            license_number="AAA123456",
            password="TestPassword123"
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
            username="test.user",
            license_number="AAA123456",
            password="TestPassword123"
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
        print(response.__dict__.keys())
