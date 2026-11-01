from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings


class ProductionStaticTests(SimpleTestCase):
    def test_collected_dashboard_uses_current_css_and_fingerprinted_url(self):
        with TemporaryDirectory() as root:
            with override_settings(
                DEBUG=False,
                STATIC_ROOT=root,
                STATICFILES_STORAGE=(
                    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
                ),
            ):
                call_command("collectstatic", interactive=False, clear=True, stdout=StringIO())
                asset = "irrigate/css/dashboard.css"
                url = Template("{% load static %}{% static asset %}").render(
                    Context({"asset": asset})
                )
                self.assertNotEqual(url, "/static/" + asset)
                collected = Path(root, url[len("/static/"):]).read_bytes()
                self.assertEqual(collected, Path(finders.find(asset)).read_bytes())
                self.assertIn(b".dashboard-shell", collected)
                self.assertTrue(staticfiles_storage.exists("irrigate/js/dashboard.js"))
