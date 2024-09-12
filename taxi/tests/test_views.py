from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from taxi.models import Manufacturer, Car, Driver

HOME_PAGE = reverse("taxi:index")
MANUFACTURER_URL = reverse("taxi:manufacturer-list")
CAR_URL = reverse("taxi:car-list")


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


class PrivetManufacturerTest(TestCase):
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

    def test_search_form(self):
        test_keys = {1: "", 2: "Audi", 3: "BMW", 4: "w"}
        Manufacturer.objects.create(name="Audi", country="Germany")
        Manufacturer.objects.create(name="BMW", country="Germany")
        Manufacturer.objects.create(name="Volkswagen", country="Germany")
        manufacturers = Manufacturer.objects.all()

        response = self.client.get(MANUFACTURER_URL, {"manufacturer": test_keys[1]})
        self.assertIn("search_form", response.context)
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

    def test_is_page_contain_paginator(self):
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
                db_q[pagination_per_page: pagination_per_page * 2],
            )

    def test_create_button(self):
        """
        Test checking:
        - The page has Create button;
        - The Create button has right url/
        """
        res = self.client.get(MANUFACTURER_URL)
        self.assertContains(res, "Create")
        self.assertContains(
            res,
            reverse("taxi:manufacturer-create"), html=False
        )

    def test_is_manufacturer_row_has_links(self):
        """
        Test that checking if a manufacturer has:
        - create link;
        - delete link.
        """
        Manufacturer.objects.create(
            name="Test Manufacturer",
            country="Test country"
        )
        res = self.client.get(MANUFACTURER_URL)
        manufacturer = Manufacturer.objects.get(
            name="Test Manufacturer"
        )
        self.assertContains(
            res,
            reverse(
                "taxi:manufacturer-update", kwargs={"pk": manufacturer.id}
            )
        )
        self.assertContains(
            res,
            reverse(
                "taxi:manufacturer-delete", kwargs={"pk": manufacturer.id}
            )
        )

    def test_update_manufacturer(self):
        """
        Test checks:
        - Is fields filled (html page contains, form initial contains);
        - Is right template used;
        - Is right page label;
        - Is manufacturer has new name and country;
        - Is redirect after update manufacturer;
        - Is right redirect page after redirect.
        """
        Manufacturer.objects.create(
            name="Test Manufacturer",
            country="Test Country"
        )
        manufacturer = Manufacturer.objects.get(id=1)
        res = self.client.get(
            reverse(
                "taxi:manufacturer-update",
                kwargs={"pk": manufacturer.id}
            )
        )
        self.assertContains(res, manufacturer.name)
        self.assertContains(res, manufacturer.country)
        self.assertEqual(
            res.context_data["form"].initial,
            {
                "id": manufacturer.id,
                "name": manufacturer.name,
                "country": manufacturer.country
            }
        )
        self.assertTemplateUsed(res, "taxi/manufacturer_form.html")
        self.assertContains(res, "Update manufacturer")
        res.context["form"].initial["name"] = "Audi"
        res.context["form"].initial["country"] = "Deutschland"
        self.client.post(
            reverse(
                "taxi:manufacturer-update",
                kwargs={"pk": manufacturer.id}
            ),
            res.context["form"].initial
        )
        self.assertEqual(manufacturer, Manufacturer.objects.get(id=1))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse("taxi:manufacturer-list"))

    def test_delete_manufacturer(self):
        """
        Test checks:
         - is on the right url;
         - is right template used;
         - is right redirect page;
         - is new manufacturer in db;
         - is deleted manufacturer from db.
         - is status code is 302;
         - is right ulr in response after post method.

        """
        Manufacturer.objects.create(
            name="Test Manufacturer",
            country="Test Country"
        )
        manufacturer = Manufacturer.objects.get(id=1)
        res = self.client.get(
            reverse(
                "taxi:manufacturer-delete",
                kwargs={"pk": manufacturer.id}
            )
        )
        self.assertEqual(
            res.context["request"].path_info,
            reverse(
                "taxi:manufacturer-delete",
                kwargs={"pk": manufacturer.id}
            )
        )
        self.assertTemplateUsed(
            res,
            "taxi/manufacturer_confirm_delete.html"
        )
        self.assertTrue(manufacturer in Manufacturer.objects.all())
        res = self.client.post(
            reverse(
                "taxi:manufacturer-delete",
                kwargs={"pk": manufacturer.id}
            )
        )
        self.assertFalse(manufacturer in Manufacturer.objects.all())
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse("taxi:manufacturer-list"))


class PublicCarTest(TestCase):
    def test_login_required(self):
        res = self.client.get(MANUFACTURER_URL)
        self.assertNotEqual(res.status_code, 200)


class PrivetCarTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test.user", license_number="AAA123456", password="TestPassword123"
        )
        self.client.force_login(self.user)

    def test_retrieve_cars(self):
        Manufacturer.objects.create(
            name="Test Manufacturer 1",
            country="Test Country",
        )
        response = self.client.get(CAR_URL)
        manufacturer = Manufacturer.objects.get(id=1)
        current_driver = Driver.objects.get(id=1)
        new_car = Car.objects.create(model="Audi", manufacturer=manufacturer)
        new_car.drivers.add(current_driver)
        new_car.save()
        # response_manufacturers = list(response.context["manufacturer_list"])
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(manufacturers, response_manufacturers)
        # self.assertTemplateUsed(response, "taxi/manufacturer_list.html")
