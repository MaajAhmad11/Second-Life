from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from donations.models import Category, Donation
from item_requests.models import DonationRequest
from connections.models import Connection

User = get_user_model()

class RequestAndConnectionFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Clothes", slug="clothes")
        self.donor = User.objects.create_user(
            email="flowdonor@secondlife.eco", password="password123", name="Flow Donor", role="DONOR"
        )
        self.receiver = User.objects.create_user(
            email="flowreceiver@secondlife.eco", password="password123", name="Flow Receiver", role="RECEIVER"
        )
        self.donation = Donation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Winter Jacket",
            description="Warm jacket",
            condition="NEW",
            status="AVAILABLE",
            location="Seattle, WA",
            city="Seattle"
        )

    def test_request_and_approval_flow(self):
        # 1. Receiver requests item
        self.client.force_authenticate(user=self.receiver)
        req_res = self.client.post('/api/requests/', {
            "donation_id": self.donation.id,
            "message": "I really need a jacket for the winter."
        }, format='json')
        self.assertEqual(req_res.status_code, status.HTTP_201_CREATED)
        req_id = req_res.data['id']

        # 2. Donor approves request
        self.client.force_authenticate(user=self.donor)
        appr_res = self.client.post(f'/api/requests/{req_id}/approve/', {
            "scheduled_date": "Saturday, 11:00 AM",
            "pickup_time_slot": "11:00 AM - 1:00 PM"
        }, format='json')
        self.assertEqual(appr_res.status_code, status.HTTP_200_OK)

        # 3. Verify Connection and Delivery created
        conn = Connection.objects.get(id=appr_res.data['connection_id'])
        self.assertEqual(conn.status, Connection.Status.ACCEPTED)
        self.assertIsNotNone(conn.delivery)
        self.assertTrue(conn.delivery.tracking_code.startswith("SL-"))

        # 4. Verify Donation marked MATCHED
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Donation.Status.MATCHED)
