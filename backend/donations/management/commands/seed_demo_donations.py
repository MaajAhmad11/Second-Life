import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Profile
from organizations.models import Organization
from donations.models import Category, Donation, DonationImage
from notifications.models import Notification
from dashboard.models import ActivityLog, ContactMessage
from chatbot.models import ChatbotFAQ


User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with realistic demo data for SecondLife platform"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.NOTICE("Seeding SecondLife database...")
        )

        # Demo data can be enabled/disabled from Render/local environment.
        # Default is true so a fresh deployment still has demo content.
        seed_demo_data = os.getenv(
            "SEED_DEMO_DATA",
            "true",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # ============================================================
        # 1. CATEGORIES
        # ============================================================

        categories_data = [
            {
                "name": "Clothes",
                "slug": "clothes",
                "icon": "Shirt",
                "description": "Gently used or new jackets, shirts, winter coats, and shoes.",
            },
            {
                "name": "Books",
                "slug": "books",
                "icon": "BookOpen",
                "description": "Textbooks, fiction, children's storybooks, and reference literature.",
            },
            {
                "name": "Electronics",
                "slug": "electronics",
                "icon": "Laptop",
                "description": "Computers, displays, desk lamps, kitchen appliances, and chargers.",
            },
            {
                "name": "Furniture",
                "slug": "furniture",
                "icon": "Armchair",
                "description": "Desks, dining tables, wooden chairs, bookshelves, and sofas.",
            },
            {
                "name": "Food",
                "slug": "food",
                "icon": "Apple",
                "description": "Canned staples, dry provisions, sealed pantry items, and produce.",
            },
            {
                "name": "Other",
                "slug": "other",
                "icon": "Package",
                "description": "Household tools, kitchenware, toys, and miscellaneous useful goods.",
            },
            {
                "name": "Bags & Accessories",
                "slug": "bags-accessories",
                "icon": "Package",
                "description": "Backpacks, bags, purses, and useful everyday accessories.",
            },
            {
                "name": "Kids & Family",
                "slug": "kids-family",
                "icon": "Package",
                "description": "Useful children's items, learning materials, and family essentials.",
            },
        ]

        categories = {}

        for cdata in categories_data:
            category, _ = Category.objects.get_or_create(
                slug=cdata["slug"],
                defaults=cdata,
            )

            categories[cdata["slug"]] = category

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(categories)} categories."
            )
        )

        # ============================================================
        # 2. ADMIN USER
        # ============================================================

        admin, _ = User.objects.get_or_create(
            email="givesthingsasecondlife@gmail.com",
            defaults={
                "name": "SecondLife Administration",
                "phone": "+92 300 0000000",
                "role": User.Role.ADMIN,
                "account_type": User.AccountType.INDIVIDUAL,
                "city": "Lahore",
                "address": "Gulberg III, Lahore",
                "country": "Pakistan",
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
                "is_active": True,
            },
        )

        admin.name = "SecondLife Administration"
        admin.phone = "+92 300 0000000"
        admin.role = User.Role.ADMIN
        admin.account_type = User.AccountType.INDIVIDUAL
        admin.city = "Lahore"
        admin.address = "Gulberg III, Lahore"
        admin.country = "Pakistan"
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_verified = True
        admin.is_active = True
        admin.set_password("Admin@12345")
        admin.save()

        Profile.objects.update_or_create(
            user=admin,
            defaults={
                "bio": "SecondLife Platform Administration",
            },
        )

        # ============================================================
        # 3-8. DEMO USERS, ORGANIZATIONS AND DONATIONS
        # Controlled by SEED_DEMO_DATA
        # ============================================================

        if seed_demo_data:

            # ========================================================
            # 3. DONORS
            # ========================================================

            donor_mamoon, _ = User.objects.get_or_create(
                email="mamoon@secondlife.eco",
                defaults={
                    "name": "Mamoon Shahid",
                    "phone": "+92 301 1111111",
                    "role": User.Role.DONOR,
                    "account_type": User.AccountType.INDIVIDUAL,
                    "city": "Lahore",
                    "address": "Johar Town, Lahore",
                    "country": "Pakistan",
                    "is_verified": True,
                    "is_active": True,
                },
            )

            donor_mamoon.name = "Mamoon Shahid"
            donor_mamoon.phone = "+92 301 1111111"
            donor_mamoon.role = User.Role.DONOR
            donor_mamoon.account_type = User.AccountType.INDIVIDUAL
            donor_mamoon.city = "Lahore"
            donor_mamoon.address = "Johar Town, Lahore"
            donor_mamoon.country = "Pakistan"
            donor_mamoon.is_verified = True
            donor_mamoon.is_active = True
            donor_mamoon.set_password("password123")
            donor_mamoon.save()

            Profile.objects.update_or_create(
                user=donor_mamoon,
                defaults={
                    "bio": "Passionate about circular economy and sustainable zero-waste living.",
                    "preferred_categories": [
                        "furniture",
                        "electronics",
                        "books",
                    ],
                    "pickup_radius": 15,
                    "handover_preference": "PICKUP",
                },
            )

            donor_sarah, _ = User.objects.get_or_create(
                email="sarah.j@secondlife.eco",
                defaults={
                    "name": "Sarah Jenkins",
                    "phone": "+92 302 2222222",
                    "role": User.Role.DONOR,
                    "account_type": User.AccountType.INDIVIDUAL,
                    "city": "Lahore",
                    "address": "Model Town, Lahore",
                    "country": "Pakistan",
                    "is_verified": True,
                    "is_active": True,
                },
            )

            donor_sarah.name = "Sarah Jenkins"
            donor_sarah.phone = "+92 302 2222222"
            donor_sarah.role = User.Role.DONOR
            donor_sarah.account_type = User.AccountType.INDIVIDUAL
            donor_sarah.city = "Lahore"
            donor_sarah.address = "Model Town, Lahore"
            donor_sarah.country = "Pakistan"
            donor_sarah.is_verified = True
            donor_sarah.is_active = True
            donor_sarah.set_password("password123")
            donor_sarah.save()

            Profile.objects.update_or_create(
                user=donor_sarah,
                defaults={
                    "bio": "Downsizing and giving durable quality home items a second life.",
                    "preferred_categories": [
                        "furniture",
                        "clothes",
                    ],
                    "pickup_radius": 10,
                    "handover_preference": "PICKUP",
                },
            )

            # ========================================================
            # ORGANIZATION DONOR
            # ========================================================

            org_donor_user, _ = User.objects.get_or_create(
                email="contact@greenearth.org",
                defaults={
                    "name": "Green Earth Foundation",
                    "phone": "+92 303 3333333",
                    "role": User.Role.DONOR,
                    "account_type": User.AccountType.ORGANIZATION,
                    "city": "Islamabad",
                    "address": "F-7, Islamabad",
                    "country": "Pakistan",
                    "is_verified": True,
                    "is_active": True,
                },
            )

            org_donor_user.name = "Green Earth Foundation"
            org_donor_user.phone = "+92 303 3333333"
            org_donor_user.role = User.Role.DONOR
            org_donor_user.account_type = User.AccountType.ORGANIZATION
            org_donor_user.city = "Islamabad"
            org_donor_user.address = "F-7, Islamabad"
            org_donor_user.country = "Pakistan"
            org_donor_user.is_verified = True
            org_donor_user.is_active = True
            org_donor_user.set_password("password123")
            org_donor_user.save()

            Profile.objects.get_or_create(
                user=org_donor_user
            )

            Organization.objects.update_or_create(
                user=org_donor_user,
                defaults={
                    "organization_name": "Green Earth Foundation",
                    "organization_type": Organization.OrgType.FOUNDATION,
                    "license_number": "PK-NGO-88219",
                    "contact_person": "David Vance",
                    "official_email": "contact@greenearth.org",
                    "phone": "+92 303 3333333",
                    "address": "F-7, Islamabad",
                    "city": "Islamabad",
                    "website": "https://greenearth.org",
                    "description": "Donating refurbished educational computers and library books to communities in need.",
                    "verification_status": Organization.VerificationStatus.VERIFIED,
                    "verified_at": timezone.now(),
                },
            )

            # ========================================================
            # 4. RECEIVERS
            # ========================================================

            receiver_alex, _ = User.objects.get_or_create(
                email="alex.rivera@secondlife.eco",
                defaults={
                    "name": "Alex Rivera",
                    "phone": "+92 304 4444444",
                    "role": User.Role.RECEIVER,
                    "account_type": User.AccountType.INDIVIDUAL,
                    "city": "Lahore",
                    "address": "DHA Phase 6, Lahore",
                    "country": "Pakistan",
                    "is_verified": True,
                    "is_active": True,
                },
            )

            receiver_alex.name = "Alex Rivera"
            receiver_alex.phone = "+92 304 4444444"
            receiver_alex.role = User.Role.RECEIVER
            receiver_alex.account_type = User.AccountType.INDIVIDUAL
            receiver_alex.city = "Lahore"
            receiver_alex.address = "DHA Phase 6, Lahore"
            receiver_alex.country = "Pakistan"
            receiver_alex.is_verified = True
            receiver_alex.is_active = True
            receiver_alex.set_password("password123")
            receiver_alex.save()

            Profile.objects.update_or_create(
                user=receiver_alex,
                defaults={
                    "bio": "Freelance eco-designer setting up a sustainable home office and community study corner.",
                    "needed_categories": [
                        "furniture",
                        "electronics",
                        "books",
                    ],
                    "pickup_radius": 12,
                    "handover_preference": "EITHER",
                },
            )

            # ========================================================
            # VERIFIED ORGANIZATION RECEIVER
            # ========================================================

            org_rec_verified_user, _ = User.objects.get_or_create(
                email="director@localyouth.org",
                defaults={
                    "name": "Local Youth Center",
                    "phone": "+92 305 5555555",
                    "role": User.Role.RECEIVER,
                    "account_type": User.AccountType.ORGANIZATION,
                    "city": "Rawalpindi",
                    "address": "Saddar, Rawalpindi",
                    "country": "Pakistan",
                    "is_verified": True,
                    "is_active": True,
                },
            )

            org_rec_verified_user.name = "Local Youth Center"
            org_rec_verified_user.phone = "+92 305 5555555"
            org_rec_verified_user.role = User.Role.RECEIVER
            org_rec_verified_user.account_type = User.AccountType.ORGANIZATION
            org_rec_verified_user.city = "Rawalpindi"
            org_rec_verified_user.address = "Saddar, Rawalpindi"
            org_rec_verified_user.country = "Pakistan"
            org_rec_verified_user.is_verified = True
            org_rec_verified_user.is_active = True
            org_rec_verified_user.set_password("password123")
            org_rec_verified_user.save()

            Profile.objects.update_or_create(
                user=org_rec_verified_user
            )

            Organization.objects.update_or_create(
                user=org_rec_verified_user,
                defaults={
                    "organization_name": "Local Youth Center",
                    "organization_type": Organization.OrgType.COMMUNITY,
                    "license_number": "PK-COMM-4410",
                    "contact_person": "Elena Marcus",
                    "official_email": "director@localyouth.org",
                    "phone": "+92 305 5555555",
                    "address": "Saddar, Rawalpindi",
                    "city": "Rawalpindi",
                    "website": "https://localyouthcenter.org",
                    "description": "Community programs providing safe learning spaces, coding workshops, and educational support for young people.",
                    "verification_status": Organization.VerificationStatus.VERIFIED,
                    "verified_at": timezone.now(),
                },
            )

            # ========================================================
            # PENDING ORGANIZATION
            # ========================================================

            org_pending_user, _ = User.objects.get_or_create(
                email="contact@newhorizon.org",
                defaults={
                    "name": "New Horizon Relief Shelter",
                    "phone": "+92 306 6666666",
                    "role": User.Role.RECEIVER,
                    "account_type": User.AccountType.ORGANIZATION,
                    "city": "Karachi",
                    "address": "Gulshan-e-Iqbal, Karachi",
                    "country": "Pakistan",
                    "is_verified": False,
                    "is_active": True,
                },
            )

            org_pending_user.name = "New Horizon Relief Shelter"
            org_pending_user.phone = "+92 306 6666666"
            org_pending_user.role = User.Role.RECEIVER
            org_pending_user.account_type = User.AccountType.ORGANIZATION
            org_pending_user.city = "Karachi"
            org_pending_user.address = "Gulshan-e-Iqbal, Karachi"
            org_pending_user.country = "Pakistan"
            org_pending_user.is_verified = False
            org_pending_user.is_active = True
            org_pending_user.set_password("password123")
            org_pending_user.save()

            Profile.objects.update_or_create(
                user=org_pending_user
            )

            Organization.objects.update_or_create(
                user=org_pending_user,
                defaults={
                    "organization_name": "New Horizon Relief Shelter",
                    "organization_type": Organization.OrgType.SHELTER,
                    "license_number": "PK-REL-99212",
                    "contact_person": "Robert Hall",
                    "official_email": "contact@newhorizon.org",
                    "phone": "+92 306 6666666",
                    "address": "Gulshan-e-Iqbal, Karachi",
                    "city": "Karachi",
                    "website": "https://newhorizonrelief.org",
                    "description": "Relief and transitional support organization helping families and individuals in difficult circumstances.",
                    "verification_status": Organization.VerificationStatus.PENDING,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Loaded demo users & organizations only."
                )
            )

            # ========================================================
            # 5-8. DEMO MARKETPLACE DONATIONS
            # ========================================================

            demo_titles = [
                "Oak Dining Chair - Solid Wood",
                "Warm Winter Jacket - Like New",
                "Canvas Travel Backpack - Everyday Carry",
                "Kids Learning Backpack & Art Set",
            ]

            removed_count, _ = Donation.objects.filter(
                title__in=demo_titles
            ).delete()

            # --------------------------------------------------------
            # Demo marketplace donors
            # --------------------------------------------------------

            demo_donors = [
                {
                    "email": "olivia.demo@secondlife.eco",
                    "name": "Olivia Khan",
                    "phone": "+92 307 7777777",
                    "city": "Lahore",
                    "address": "Johar Town, Lahore",
                    "bio": "Sharing quality home items that still have plenty of life left.",
                },
                {
                    "email": "ethan.demo@secondlife.eco",
                    "name": "Ahmed Hassan",
                    "phone": "+92 308 8888888",
                    "city": "Islamabad",
                    "address": "F-7, Islamabad",
                    "bio": "Giving useful clothing a second life instead of letting it go to waste.",
                },
                {
                    "email": "mia.demo@secondlife.eco",
                    "name": "Ayesha Malik",
                    "phone": "+92 309 9999999",
                    "city": "Rawalpindi",
                    "address": "Saddar, Rawalpindi",
                    "bio": "Passing on practical bags and accessories that are still in great condition.",
                },
                {
                    "email": "liam.demo@secondlife.eco",
                    "name": "Hamza Ali",
                    "phone": "+92 310 1234567",
                    "city": "Karachi",
                    "address": "Gulshan-e-Iqbal, Karachi",
                    "bio": "Helping families reuse educational and creative items.",
                },
            ]

            donors = {}

            for donor_data in demo_donors:
                donor, _ = User.objects.get_or_create(
                    email=donor_data["email"],
                    defaults={
                        "name": donor_data["name"],
                        "phone": donor_data["phone"],
                        "role": User.Role.DONOR,
                        "account_type": User.AccountType.INDIVIDUAL,
                        "city": donor_data["city"],
                        "address": donor_data["address"],
                        "country": "Pakistan",
                        "is_verified": True,
                        "is_active": True,
                    },
                )

                donor.name = donor_data["name"]
                donor.phone = donor_data["phone"]
                donor.role = User.Role.DONOR
                donor.account_type = User.AccountType.INDIVIDUAL
                donor.city = donor_data["city"]
                donor.address = donor_data["address"]
                donor.country = "Pakistan"
                donor.is_verified = True
                donor.is_active = True
                donor.set_password("password123")
                donor.save()

                Profile.objects.update_or_create(
                    user=donor,
                    defaults={
                        "bio": donor_data["bio"],
                        "pickup_radius": 15,
                        "handover_preference": "PICKUP",
                    },
                )

                donors[donor_data["email"]] = donor

            # --------------------------------------------------------
            # Extra marketplace categories
            # --------------------------------------------------------

            extra_categories = [
                {
                    "name": "Bags & Accessories",
                    "slug": "bags-accessories",
                    "icon": "Package",
                    "description": "Backpacks, bags, purses, and useful everyday accessories.",
                },
                {
                    "name": "Kids & Family",
                    "slug": "kids-family",
                    "icon": "Package",
                    "description": "Useful children's items, learning materials, and family essentials.",
                },
            ]

            for cdata in extra_categories:
                category, _ = Category.objects.get_or_create(
                    slug=cdata["slug"],
                    defaults=cdata,
                )

                categories[cdata["slug"]] = category

            # --------------------------------------------------------
            # Marketplace donations
            # --------------------------------------------------------

            demo_donations = [
                {
                    "title": "Oak Dining Chair - Solid Wood",
                    "description": (
                        "Sturdy solid-wood dining chair with a clean finish. "
                        "Ready for a new home and everyday use."
                    ),
                    "condition": Donation.Condition.GOOD,
                    "quantity": 1,
                    "delivery_option": Donation.DeliveryOption.PICKUP,
                    "location": "Johar Town, Lahore",
                    "city": "Lahore",
                    "weight": "4.2 kg",
                    "pickup_date": "Flexible",
                    "pickup_time": "10:00 AM - 6:00 PM",
                    "category": categories["furniture"],
                    "donor": donors["olivia.demo@secondlife.eco"],
                    "image_url": "/images/donations/chair.jpg",
                },
                {
                    "title": "Warm Winter Jacket - Like New",
                    "description": (
                        "Comfortable insulated winter jacket in excellent condition, "
                        "suitable for cool-weather days."
                    ),
                    "condition": Donation.Condition.LIKE_NEW,
                    "quantity": 1,
                    "delivery_option": Donation.DeliveryOption.EITHER,
                    "location": "F-7, Islamabad",
                    "city": "Islamabad",
                    "weight": "1.1 kg",
                    "pickup_date": "This weekend",
                    "pickup_time": "11:00 AM - 5:00 PM",
                    "category": categories["clothes"],
                    "donor": donors["ethan.demo@secondlife.eco"],
                    "image_url": "/images/donations/jacket.jpg",
                },
                {
                    "title": "Canvas Travel Backpack - Everyday Carry",
                    "description": (
                        "Durable canvas backpack with roomy compartments for school, "
                        "work, or everyday travel."
                    ),
                    "condition": Donation.Condition.GOOD,
                    "quantity": 1,
                    "delivery_option": Donation.DeliveryOption.PICKUP,
                    "location": "Saddar, Rawalpindi",
                    "city": "Rawalpindi",
                    "weight": "0.9 kg",
                    "pickup_date": "Flexible",
                    "pickup_time": "9:00 AM - 4:00 PM",
                    "category": categories["bags-accessories"],
                    "donor": donors["mia.demo@secondlife.eco"],
                    "image_url": "/images/donations/bags.jpg",
                },
                {
                    "title": "Kids Learning Backpack & Art Set",
                    "description": (
                        "A practical children's backpack bundled with a reusable art "
                        "set for school and creative activities."
                    ),
                    "condition": Donation.Condition.LIKE_NEW,
                    "quantity": 1,
                    "delivery_option": Donation.DeliveryOption.PICKUP,
                    "location": "Gulshan-e-Iqbal, Karachi",
                    "city": "Karachi",
                    "weight": "1.4 kg",
                    "pickup_date": "Next week",
                    "pickup_time": "12:00 PM - 6:00 PM",
                    "category": categories["kids-family"],
                    "donor": donors["liam.demo@secondlife.eco"],
                    "image_url": "/images/donations/kids-accessories.jpg",
                },
            ]

            for data in demo_donations:
                donation = Donation.objects.create(
                    donor=data["donor"],
                    category=data["category"],
                    title=data["title"],
                    description=data["description"],
                    condition=data["condition"],
                    quantity=data["quantity"],
                    delivery_option=data["delivery_option"],
                    location=data["location"],
                    city=data["city"],
                    status=Donation.Status.AVAILABLE,
                    weight=data["weight"],
                    pickup_date=data["pickup_date"],
                    pickup_time=data["pickup_time"],
                )

                DonationImage.objects.create(
                    donation=donation,
                    image_url=data["image_url"],
                    is_primary=True,
                )

            # --------------------------------------------------------
            # Clean old demo notifications
            # --------------------------------------------------------

            Notification.objects.filter(
                user__email__in=[
                    "alex.rivera@secondlife.eco",
                    "mamoon@secondlife.eco",
                ],
                title__in=[
                    "Driver Arriving Soon 🚚",
                    "Match Confirmed! 🎉",
                    "New Item Request! 📬",
                ],
            ).delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Removed {removed_count} old demo donations and created "
                    f"{len(demo_donations)} marketplace demo donations. "
                    "They are visible on the landing page, receiver browse page, "
                    "and admin donation list."
                )
            )

        else:
            self.stdout.write(
                self.style.WARNING(
                    "SEED_DEMO_DATA is disabled. Demo users, organizations, "
                    "and donations were not seeded."
                )
            )

        # ============================================================
        # 9. ACTIVITY LOG
        # ============================================================

        ActivityLog.objects.get_or_create(
            user=admin,
            action="SYSTEM_INIT",
            defaults={
                "description": (
                    "SecondLife platform initialized with categories and "
                    "chatbot FAQs. Demo accounts/donations are controlled "
                    "by SEED_DEMO_DATA."
                )
            },
        )

        # ============================================================
        # 10. SAMPLE CONTACT MESSAGE
        # ============================================================

        ContactMessage.objects.get_or_create(
            email="maria.santos@greenpartners.org",
            defaults={
                "name": "Maria Santos",
                "subject": "Bulk Donation Logistics Partnership",
                "message": (
                    "We represent a network of local community libraries "
                    "and would like to coordinate monthly bulk book collections."
                ),
                "is_resolved": False,
            },
        )

        # ============================================================
        # 11. CHATBOT FAQs
        # ============================================================

        chatbot_faqs = [
            {
                "question": "Who developed SecondLife?",
                "answer": (
                    "SecondLife was developed by:\n\n"
                    "👨‍💻 Mamoon Shahid\n"
                    "👨‍💻 Habib Ahmad Siddiqui\n"
                    "👨‍💻 Amaaj Ahmad\n\n"
                    "Together, the team developed SecondLife — Give Things a Second Life, "
                    "a platform designed to connect donors with people and organizations "
                    "who need useful items."
                ),
                "keywords": (
                    "developer, developers, developed by, created by, creator, "
                    "who made, who created, development team, team, mamoon, "
                    "habib, amaaj"
                ),
                "category": "team",
                "priority": 100,
            },
            {
                "question": "What is SecondLife?",
                "answer": (
                    "SecondLife is a resource-sharing and donation platform that "
                    "connects people who want to donate useful items with people "
                    "and organizations who need them."
                ),
                "keywords": (
                    "what is secondlife, what is second life, about secondlife, "
                    "about second life, explain secondlife"
                ),
                "category": "general",
                "priority": 90,
            },
            {
                "question": "What is the purpose of SecondLife?",
                "answer": (
                    "The purpose of SecondLife is to give useful items a second life "
                    "by connecting donors with people and organizations that need them. "
                    "It also promotes reuse, reduces waste, and supports a circular economy."
                ),
                "keywords": (
                    "purpose, goal, objective, aim, why secondlife, "
                    "why was secondlife created"
                ),
                "category": "general",
                "priority": 80,
            },
            {
                "question": "How does SecondLife work?",
                "answer": (
                    "SecondLife works by connecting donors and receivers. "
                    "Donors can list useful items, while receivers or organizations "
                    "can browse available donations and request items they need."
                ),
                "keywords": (
                    "how does secondlife work, how it works, working, "
                    "process, platform process"
                ),
                "category": "general",
                "priority": 80,
            },
            {
                "question": "How can I donate an item?",
                "answer": (
                    "To donate an item, log in to your SecondLife account, "
                    "open the donation section, provide the item details, "
                    "select the appropriate category, add an image if available, "
                    "and submit your donation."
                ),
                "keywords": (
                    "how to donate, how can i donate, add donation, "
                    "create donation, donate item, list item"
                ),
                "category": "donations",
                "priority": 80,
            },
            {
                "question": "What can I donate?",
                "answer": (
                    "You can donate useful items such as clothes, books, furniture, "
                    "electronics, household items, educational materials, food, "
                    "and other safe items that are in usable condition."
                ),
                "keywords": (
                    "what can i donate, donation items, items to donate, "
                    "what items, donate things"
                ),
                "category": "donations",
                "priority": 75,
            },
            {
                "question": "How can I request an item?",
                "answer": (
                    "To request an item, log in to your account, browse the available "
                    "donations, open the item you need, and submit a request if it "
                    "is available."
                ),
                "keywords": (
                    "how to request, how can i request, request item, "
                    "request donation, need item, receiver request"
                ),
                "category": "requests",
                "priority": 80,
            },
            {
                "question": "Who can receive donations?",
                "answer": (
                    "Individuals and eligible organizations can receive donations "
                    "through SecondLife. Receivers can browse available items "
                    "and request items that meet their needs."
                ),
                "keywords": (
                    "who can receive, receiver, receivers, recipient, "
                    "who gets donations"
                ),
                "category": "requests",
                "priority": 70,
            },
            {
                "question": "Can organizations use SecondLife?",
                "answer": (
                    "Yes. Organizations can use SecondLife to donate useful items "
                    "or request items for their communities, programs, shelters, "
                    "and other legitimate needs."
                ),
                "keywords": (
                    "organization, organizations, ngo, charity, "
                    "institution, foundation"
                ),
                "category": "organizations",
                "priority": 75,
            },
            {
                "question": "How does matching work?",
                "answer": (
                    "SecondLife helps connect available donations with people or "
                    "organizations looking for those items. Matching can consider "
                    "factors such as item category, availability, location, "
                    "and the receiver's needs."
                ),
                "keywords": (
                    "matching, match, matches, how matching works, "
                    "donor receiver matching"
                ),
                "category": "matching",
                "priority": 70,
            },
            {
                "question": "Is SecondLife free?",
                "answer": (
                    "SecondLife is designed as a donation and resource-sharing "
                    "platform. Users can use the platform to discover available "
                    "items and connect with donors or receivers."
                ),
                "keywords": (
                    "free, cost, costs, charges, price, payment, fee"
                ),
                "category": "general",
                "priority": 60,
            },
            {
                "question": "Why should I donate?",
                "answer": (
                    "Donating useful items can help people and organizations in need, "
                    "reduce unnecessary waste, encourage reuse, and give valuable "
                    "items a second life."
                ),
                "keywords": (
                    "why donate, benefits of donating, donation benefits, "
                    "reason to donate"
                ),
                "category": "donations",
                "priority": 65,
            },
            {
                "question": "What donation categories are available?",
                "answer": (
                    "SecondLife currently supports categories such as Clothes, "
                    "Books, Electronics, Furniture, Food, Bags & Accessories, "
                    "Kids & Family, and Other useful items."
                ),
                "keywords": (
                    "categories, donation categories, item categories, "
                    "types of donations, available categories"
                ),
                "category": "donations",
                "priority": 65,
            },
            {
                "question": "Can I donate electronics?",
                "answer": (
                    "Yes. Useful electronics can be donated through SecondLife. "
                    "Please make sure the item is safe, functional, and accurately "
                    "described before listing it."
                ),
                "keywords": (
                    "electronics, electronic items, donate electronics, "
                    "laptop, computer, phone"
                ),
                "category": "donations",
                "priority": 60,
            },
            {
                "question": "Can I donate clothes?",
                "answer": (
                    "Yes. Clothes can be donated through SecondLife. "
                    "It is best to donate clothing that is clean, safe, "
                    "and in usable condition."
                ),
                "keywords": (
                    "clothes, clothing, donate clothes, shirts, jackets, shoes"
                ),
                "category": "donations",
                "priority": 60,
            },
            {
                "question": "How does delivery work?",
                "answer": (
                    "Depending on the donation, handover may be arranged through "
                    "pickup, delivery, or an available option agreed by the users. "
                    "Connection and delivery information can be used to track the process."
                ),
                "keywords": (
                    "delivery, deliver, pickup, pick up, handover, "
                    "transport, courier"
                ),
                "category": "delivery",
                "priority": 65,
            },
            {
                "question": "Is my information safe?",
                "answer": (
                    "Users should protect their account credentials and only share "
                    "necessary information through the platform. Avoid sharing "
                    "passwords or sensitive personal information with other users."
                ),
                "keywords": (
                    "safe, safety, information safe, privacy, secure, "
                    "security, personal information"
                ),
                "category": "safety",
                "priority": 65,
            },
            {
                "question": "How do I create an account?",
                "answer": (
                    "You can create an account through the SecondLife registration "
                    "process. Provide the required information, choose the appropriate "
                    "account type, and complete registration."
                ),
                "keywords": (
                    "create account, register, registration, sign up, signup, "
                    "new account"
                ),
                "category": "accounts",
                "priority": 60,
            },
            {
                "question": "What is the environmental benefit of SecondLife?",
                "answer": (
                    "SecondLife encourages reuse and helps keep useful items "
                    "in circulation instead of sending them to waste. "
                    "This supports a more sustainable and circular economy."
                ),
                "keywords": (
                    "environment, environmental, sustainability, sustainable, "
                    "waste, recycle, reuse, circular economy"
                ),
                "category": "general",
                "priority": 65,
            },
        ]

        for faq in chatbot_faqs:
            ChatbotFAQ.objects.update_or_create(
                question=faq["question"],
                defaults={
                    "answer": faq["answer"],
                    "keywords": faq["keywords"],
                    "category": faq["category"],
                    "is_active": True,
                    "priority": faq["priority"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(chatbot_faqs)} chatbot FAQs."
            )
        )

        # ============================================================
        # FINISHED
        # ============================================================

        self.stdout.write(
            self.style.SUCCESS(
                "SecondLife seed data successfully loaded!"
            )
        )