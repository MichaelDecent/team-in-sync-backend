import pytest
from django.test import Client, TestCase


class CORSTest(TestCase):
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        client = Client(HTTP_ORIGIN="http://localhost:3000")
        response = client.options(
            "/api/v1/users/register/", HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("Access-Control-Allow-Origin"))
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "http://localhost:3000"
        )


@pytest.mark.django_db
class TestCORSWithPytest:
    """Test CORS configuration with pytest"""

    def test_cors_headers_pytest(self, client):
        """Test that CORS headers are properly set using pytest"""
        headers = {
            "HTTP_ORIGIN": "http://localhost:3000",
            "HTTP_ACCESS_CONTROL_REQUEST_METHOD": "POST",
        }
        response = client.options("/api/v1/users/register/", **headers)

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response
        assert response["Access-Control-Allow-Origin"] == "http://localhost:3000"
