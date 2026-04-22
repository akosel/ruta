from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardAuthTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_dashboard_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="ruta", password="correct-password"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irrigate/dashboard.html")

    def test_login_redirects_authenticated_user_to_dashboard(self):
        get_user_model().objects.create_user(
            username="ruta", password="correct-password"
        )

        response = self.client.post(
            reverse("login"),
            {"username": "ruta", "password": "correct-password"},
        )

        self.assertRedirects(response, reverse("dashboard"))
