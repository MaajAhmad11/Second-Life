from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from donations.models import Category, Donation
from services.matching_service import MatchingService
from accounts.models import Profile

User = get_user_model()

class DonationsAndMatchingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Furniture", slug="furniture")
        self.donor = User.objects.create_user(
            email="donor1@secondlife.eco", password="password123", name="Donor 1", role="DONOR", city="Seattle"
        )
        self.receiver = User.objects.create_user(
            email="rec1@secondlife.eco", password="password123", name="Receiver 1", role="RECEIVER", city="Seattle"
        )
        Profile.objects.create(
            user=self.receiver,
            needed_categories=["furniture"],
            pickup_radius=15,
            handover_preference="PICKUP"
        )
        self.donation = Donation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Wooden Coffee Table",
            description="Good table",
            condition="LIKE_NEW",
            delivery_option="PICKUP",
            location="Seattle, WA",
            city="Seattle",
            status="AVAILABLE"
        )

    def test_matching_score_calculation(self):
        match_result = MatchingService.calculate_match_score(self.donation, self.receiver)
        self.assertGreaterEqual(match_result['score'], 80)
        self.assertTrue(match_result['is_recommended'])

    def test_browse_donations_public_api(self):
        res = self.client.get('/api/donations/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_donor_can_create_donation(self):
        self.client.force_authenticate(user=self.donor)
        payload = {
            "title": "Vintage Bookshelf",
            "description": "5 shelves solid pine",
            "category_id": self.category.id,
            "condition": "GOOD",
            "quantity": 1,
            "delivery_option": "PICKUP",
            "location": "Downtown Seattle",
            "city": "Seattle"
        }
        res = self.client.post('/api/donations/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Donation.objects.filter(title="Vintage Bookshelf").count(), 1)
