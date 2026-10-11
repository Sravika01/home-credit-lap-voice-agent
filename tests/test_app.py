"""Automated tests for the Flask eligibility demo application (app.py)."""

import unittest
from app import app


class TestFlaskEligibilityApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_home_page(self):
        """GET / should render the form with HTTP 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Home Credit", content)
        self.assertIn("Loan Against Property", content)
        self.assertIn("Check eligibility", content)

    def test_post_eligible_scenario(self):
        """POST / with compliant inputs should return 'Potentially eligible'."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Salaried bank credited",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Potentially eligible", content)
        self.assertIn("senior loan expert", content)

    def test_post_commercial_eligible(self):
        """Commercial property with compliant inputs should pass."""
        data = {
            "property_type": "Commercial",
            "ownership": "Joint",
            "documents": "Available",
            "occupation": "Self-employed bank credited",
            "loan_amount": "5000000",
            "property_value": "10000000",
            "tenure": "7",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Potentially eligible", content)

    def test_post_agricultural_disqualification(self):
        """Agricultural property must be disqualified immediately."""
        data = {
            "property_type": "Agricultural",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Salaried bank credited",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Disqualified", content)
        self.assertIn("Only residential and commercial properties are eligible.", content)

    def test_post_industrial_disqualification(self):
        """Industrial property must be disqualified immediately."""
        data = {
            "property_type": "Industrial",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Salaried bank credited",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Disqualified", content)
        self.assertIn("Only residential and commercial properties are eligible.", content)

    def test_post_held_by_lender_referral(self):
        """Original documents held by lender must trigger specialist referral."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Held by lender",
            "occupation": "Salaried bank credited",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Specialist referral", content)
        self.assertIn("loan-transfer specialist", content)

    def test_post_unavailable_documents(self):
        """Unavailable documents must trigger disqualification."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Unavailable",
            "occupation": "Salaried bank credited",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Disqualified", content)
        self.assertIn("Original property documents must be available.", content)

    def test_post_cash_income_disqualification(self):
        """Cash income must trigger disqualification."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Cash income",
            "loan_amount": "2500000",
            "property_value": "5000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Disqualified", content)
        self.assertIn("Income must be credited to a bank account.", content)

    def test_post_loan_amount_exceeds_cap(self):
        """Amount above ₹75 lakh cap must trigger cap explanation."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Salaried bank credited",
            "loan_amount": "8000000",
            "property_value": "20000000",
            "tenure": "10",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Loan amount exceeds cap", content)
        self.assertIn("maximum offer is ₹75,00,000", content)

    def test_post_tenure_out_of_range(self):
        """Tenure below 3 or above 15 years must be disqualified."""
        for bad_tenure in ["2", "16", "20"]:
            data = {
                "property_type": "Residential",
                "ownership": "Sole",
                "documents": "Available",
                "occupation": "Salaried bank credited",
                "loan_amount": "2500000",
                "property_value": "5000000",
                "tenure": bad_tenure,
            }
            response = self.client.post("/", data=data)
            self.assertEqual(response.status_code, 200)
            content = response.data.decode("utf-8")
            self.assertIn("Disqualified", content)
            self.assertIn("eligible tenure range is 3 to 15 years", content)

    def test_post_invalid_number_handling(self):
        """Non-numeric input must be caught gracefully without crashing with HTTP 500."""
        data = {
            "property_type": "Residential",
            "ownership": "Sole",
            "documents": "Available",
            "occupation": "Salaried bank credited",
            "loan_amount": "invalid_amount",
            "property_value": "five lakh",
            "tenure": "abc",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Invalid input", content)
        self.assertIn("must be valid whole numbers", content)


if __name__ == "__main__":
    unittest.main()

