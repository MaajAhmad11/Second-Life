import re
from difflib import SequenceMatcher

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import ChatbotFAQ


class ChatbotAssistantView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    # =========================================================
    # DEFAULT / FALLBACK RESPONSE
    # =========================================================

    DEFAULT_RESPONSE = (
        "I'm the SecondLife Assistant 🌿🤖\n\n"
        "I can help you with information about SecondLife, donations, "
        "receivers, registration, organizations, matching, connections, "
        "delivery, safety, accounts, and our development team.\n\n"
        "Try asking:\n"
        "• What is SecondLife?\n"
        "• Who developed SecondLife?\n"
        "• What can I donate?\n"
        "• How do I donate an item?\n"
        "• How do I request an item?\n"
        "• How does matching work?\n"
        "• How do I register?\n"
        "• Can organizations donate?\n"
        "• Is SecondLife free?\n"
        "• How does delivery work?"
    )

    DEFAULT_SUGGESTIONS = [
        "What is SecondLife?",
        "Who developed SecondLife?",
        "What can I donate?",
        "How do I donate an item?",
        "How do I request an item?",
        "How does matching work?",
    ]

    # =========================================================
    # OFFICIAL DEVELOPMENT TEAM
    # =========================================================

    DEVELOPER_RESPONSE = (
        "SecondLife was developed by our team: 🌿🤖\n\n"
        "• Mamoon Shahid\n"
        "• Habib Ahmad Siddiqui\n"
        "• Maaj Ahmad\n\n"
        "We created SecondLife as a circular resource-sharing and "
        "donation platform connecting individuals and organizations "
        "who have useful items with those who need them.\n\n"
        "Our goal is to extend product lifecycles, reduce unnecessary "
        "waste, and build stronger communities through transparent "
        "and zero-fee digital handovers."
    )

    DEVELOPER_SUGGESTIONS = [
        "What is SecondLife?",
        "What can I donate?",
        "How do I donate an item?",
        "How do I request an item?",
        "How does matching work?",
    ]

    # =========================================================
    # SECOND LIFE KNOWLEDGE BASE
    # =========================================================

    KNOWLEDGE_BASE = [

        # =====================================================
        # GENERAL / ABOUT SECOND LIFE
        # =====================================================

        {
            "patterns": [
                r"\bwhat is secondlife\b",
                r"\bwhat is secondlife platform\b",
                r"\btell me about secondlife\b",
                r"\babout secondlife\b",
                r"\bwhat is this platform\b",
                r"\bwhat is this website\b",
            ],
            "answer": (
                "SecondLife — Give Things a Second Life 🌿\n\n"
                "SecondLife is a circular resource-sharing and donation "
                "platform connecting individuals and organizations who "
                "have useful items with those who need them.\n\n"
                "Our mission is to eliminate landfill waste, extend "
                "product lifecycles, and build stronger, more sustainable "
                "communities through transparent, zero-fee digital handovers."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bwhat is the mission of secondlife\b",
                r"\bsecondlife mission\b",
                r"\bmission of secondlife\b",
            ],
            "answer": (
                "The mission of SecondLife is to create a more circular "
                "and sustainable approach to resource sharing.\n\n"
                "We aim to reduce landfill waste, extend product lifecycles, "
                "and connect useful resources with people and organizations "
                "that need them."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bwhat is the goal of secondlife\b",
                r"\bgoal of secondlife\b",
                r"\bpurpose of secondlife\b",
                r"\bwhy was secondlife created\b",
            ],
            "answer": (
                "SecondLife was created to make resource sharing and "
                "donations more accessible, organized, and transparent.\n\n"
                "The platform helps useful items move from people or "
                "organizations that no longer need them to those who "
                "can benefit from them."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bhow does secondlife work\b",
                r"\bhow does the platform work\b",
                r"\bsecondlife workflow\b",
                r"\bhow does this platform work\b",
            ],
            "answer": (
                "SecondLife follows a simple four-stage model:\n\n"
                "Donate → Match → Deliver → Impact 🌿\n\n"
                "Donors list useful items, the platform helps identify "
                "suitable receivers, the relevant parties proceed toward "
                "a digital handover, and the donated item gets a second life."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bwhy is it called secondlife\b",
                r"\bmeaning of secondlife\b",
                r"\bwhat does secondlife mean\b",
            ],
            "answer": (
                "The name SecondLife represents our core idea: giving "
                "useful products a second life instead of allowing them "
                "to become unnecessary waste.\n\n"
                "An item that is no longer useful to one person may still "
                "have significant value to another."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bwhat makes secondlife different\b",
                r"\bwhat is unique about secondlife\b",
                r"\bwhy secondlife\b",
            ],
            "answer": (
                "SecondLife focuses on circular resource sharing rather "
                "than traditional buying and selling.\n\n"
                "The platform is designed to connect useful surplus items "
                "with people and organizations that need them through a "
                "structured and transparent digital process."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bwhat are the benefits of secondlife\b",
                r"\bbenefits of secondlife\b",
                r"\bhow does secondlife help people\b",
                r"\bhow can secondlife help\b",
            ],
            "answer": (
                "SecondLife helps make resource sharing more organized "
                "and accessible.\n\n"
                "It can help useful items reach people and organizations "
                "that need them while encouraging reuse, extending product "
                "lifecycles, and reducing unnecessary waste."
            ),
            "category": "general",
        },

        # =====================================================
        # DEVELOPMENT TEAM
        # =====================================================

        {
            "patterns": [
                r"\bwho developed secondlife\b",
                r"\bwho develop secondlife\b",
                r"\bwho developed secondlife platform\b",
                r"\bwho created secondlife\b",
                r"\bwho created the secondlife\b",
                r"\bwho made secondlife\b",
                r"\bwho built secondlife\b",
                r"\bsecondlife developer\b",
                r"\bsecondlife developers\b",
                r"\bsecondlife development team\b",
                r"\bdevelopers of secondlife\b",
                r"\bcreator of secondlife\b",
                r"\bcreators of secondlife\b",
                r"\bteam behind secondlife\b",
                r"\bwho is behind secondlife\b",
                r"\bwho are behind secondlife\b",
            ],
            "answer": DEVELOPER_RESPONSE,
            "category": "team",
        },

        {
            "patterns": [
                r"\bwho founded secondlife\b",
                r"\bfounder of secondlife\b",
                r"\bsecondlife founder\b",
            ],
            "answer": (
                "SecondLife was initiated and developed as a collaborative "
                "project by:\n\n"
                "• Mamoon Shahid\n"
                "• Habib Ahmad Siddiqui\n"
                "• Maaj Ahmad\n\n"
                "The team built SecondLife around the principles of reuse, "
                "resource sharing, accessibility, and community impact."
            ),
            "category": "team",
        },

        # =====================================================
        # DONOR
        # =====================================================

        {
            "patterns": [
                r"\bwhat is a donor\b",
                r"\bwho is a donor\b",
                r"\bwhat does donor mean\b",
            ],
            "answer": (
                "A donor is an individual or organization that has a useful "
                "item they no longer need and wants to make that item "
                "available to someone who can use it."
            ),
            "category": "donor",
        },

        {
            "patterns": [
                r"\bhow do i become a donor\b",
                r"\bhow can i become a donor\b",
                r"\bbecome donor\b",
                r"\bdonor registration\b",
                r"\bregister as donor\b",
            ],
            "answer": (
                "To become a donor, select the Donor option during "
                "registration and provide the required information.\n\n"
                "Once your account is created, you can use the donor "
                "dashboard to list useful items for sharing."
            ),
            "category": "donor",
        },

        {
            "patterns": [
                r"\bhow do i donate\b",
                r"\bhow can i donate\b",
                r"\bhow to donate\b",
                r"\bdonate an item\b",
                r"\bi want to donate\b",
                r"\bi want to give an item\b",
            ],
            "answer": (
                "To donate an item through SecondLife:\n\n"
                "1. Register or log in as a Donor.\n"
                "2. Open the donation section.\n"
                "3. Select the appropriate category.\n"
                "4. Add the item's details and condition.\n"
                "5. Provide any requested images or information.\n"
                "6. Submit the donation.\n\n"
                "Your listing can then become available for suitable matching."
            ),
            "category": "donor",
        },

        {
            "patterns": [
                r"\bcan anyone donate\b",
                r"\bwho can donate\b",
                r"\bwho is allowed to donate\b",
            ],
            "answer": (
                "Individuals and eligible organizations can participate "
                "as donors through SecondLife.\n\n"
                "Donors should provide accurate information and ensure "
                "that their items are safe and suitable for reuse."
            ),
            "category": "donor",
        },

        {
            "patterns": [
                r"\bcan i donate multiple items\b",
                r"\bcan i donate many items\b",
                r"\bmultiple donations\b",
                r"\bmore than one item\b",
            ],
            "answer": (
                "Yes. Donors can share multiple useful items through "
                "SecondLife, subject to the platform's current donation "
                "workflow and category requirements.\n\n"
                "Each item should have accurate details so it can be "
                "properly considered for matching."
            ),
            "category": "donor",
        },

        # =====================================================
        # DONATION CATEGORIES
        # =====================================================

        {
            "patterns": [
                r"\bwhat can i donate\b",
                r"\bwhat items can i donate\b",
                r"\bwhat things can i donate\b",
                r"\bwhich items can be donated\b",
                r"\bwhat type of items can i donate\b",
            ],
            "answer": (
                "SecondLife supports several useful resource categories:\n\n"
                "👕 Clothes\n"
                "📚 Books\n"
                "💻 Electronics\n"
                "🪑 Furniture\n"
                "🍱 Food\n\n"
                "Items should be safe, usable, and accurately described."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate clothes\b",
                r"\bclothes donation\b",
                r"\bdonate clothing\b",
                r"\bcan i give clothes\b",
            ],
            "answer": (
                "Yes. Clothes are one of the supported SecondLife categories.\n\n"
                "Donated clothing should preferably be clean, usable, and "
                "described accurately so receivers know what they are requesting."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate books\b",
                r"\bbook donation\b",
                r"\bdonate books\b",
                r"\bcan i give books\b",
            ],
            "answer": (
                "Yes. Books can be shared through SecondLife.\n\n"
                "Donors can provide useful books that are in reasonable "
                "condition for individuals or organizations that may need them."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate electronics\b",
                r"\belectronics donation\b",
                r"\bdonate electronics\b",
                r"\bcan i give electronics\b",
            ],
            "answer": (
                "Yes. Electronics are supported as a donation category.\n\n"
                "Please provide accurate information about the device, "
                "including its condition and functionality."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate furniture\b",
                r"\bfurniture donation\b",
                r"\bdonate furniture\b",
                r"\bcan i give furniture\b",
            ],
            "answer": (
                "Yes. Furniture can be offered through SecondLife.\n\n"
                "Donors should provide useful details such as the furniture "
                "type, condition, approximate size, and availability."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate food\b",
                r"\bfood donation\b",
                r"\bdonate food\b",
                r"\bcan i give food\b",
            ],
            "answer": (
                "Yes. Food is included among the supported SecondLife "
                "categories.\n\n"
                "Food donations should be appropriate for donation and "
                "handled responsibly according to applicable safety requirements."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate used items\b",
                r"\bcan i donate old items\b",
                r"\bused item donation\b",
                r"\bold item donation\b",
                r"\bcan i donate second hand items\b",
            ],
            "answer": (
                "Yes. SecondLife is designed to extend the useful life "
                "of products.\n\n"
                "Used items can be donated when they remain safe and usable. "
                "Their condition should be described honestly."
            ),
            "category": "donation",
        },

        {
            "patterns": [
                r"\bcan i donate damaged items\b",
                r"\bcan i donate broken items\b",
                r"\bdamaged donation\b",
                r"\bbroken donation\b",
            ],
            "answer": (
                "Damaged or broken items should only be offered when their "
                "condition is clearly disclosed and the item remains useful "
                "for repair or another appropriate purpose.\n\n"
                "Items that are unsafe or hazardous should not be donated."
            ),
            "category": "safety",
        },

        {
            "patterns": [
                r"\bwhat should i not donate\b",
                r"\bwhat cannot be donated\b",
                r"\bprohibited items\b",
                r"\bitems not allowed\b",
                r"\bwhich items are prohibited\b",
            ],
            "answer": (
                "Items that are illegal, dangerous, hazardous, or unsafe "
                "should not be donated through SecondLife.\n\n"
                "If you are uncertain about an item, review the platform's "
                "current donation rules before submitting it."
            ),
            "category": "safety",
        },

        # =====================================================
        # RECEIVER
        # =====================================================

        {
            "patterns": [
                r"\bwhat is a receiver\b",
                r"\bwho is a receiver\b",
                r"\bwhat does receiver mean\b",
            ],
            "answer": (
                "A receiver is an individual or organization that needs "
                "a useful item and submits a request through SecondLife."
            ),
            "category": "receiver",
        },

        {
            "patterns": [
                r"\bhow do i become a receiver\b",
                r"\bhow can i become a receiver\b",
                r"\bregister as receiver\b",
                r"\breceiver registration\b",
            ],
            "answer": (
                "To become a receiver, select the Receiver option during "
                "registration and provide the required information.\n\n"
                "After registration, you can use the receiver dashboard "
                "to request items that you need."
            ),
            "category": "receiver",
        },

        {
            "patterns": [
                r"\bhow do i request an item\b",
                r"\bhow can i request an item\b",
                r"\bhow to request an item\b",
                r"\brequest a donation\b",
                r"\bi need an item\b",
                r"\bi need something\b",
            ],
            "answer": (
                "To request an item through SecondLife:\n\n"
                "1. Register or log in as a Receiver.\n"
                "2. Open the request section.\n"
                "3. Select the relevant category.\n"
                "4. Describe the item you need.\n"
                "5. Provide the requested information.\n"
                "6. Submit your request.\n\n"
                "Suitable available donations can then be considered for matching."
            ),
            "category": "receiver",
        },

        {
            "patterns": [
                r"\bwho can receive donations\b",
                r"\bwho can receive items\b",
                r"\bwho is eligible to receive\b",
                r"\bwho can receive\b",
            ],
            "answer": (
                "Individuals and eligible organizations that need useful "
                "items can participate as receivers, subject to the "
                "platform's registration and verification requirements."
            ),
            "category": "receiver",
        },

        {
            "patterns": [
                r"\bcan i request more than one item\b",
                r"\bcan i request multiple items\b",
                r"\bmultiple requests\b",
            ],
            "answer": (
                "Multiple requests may be possible depending on the "
                "platform's current workflow and account rules.\n\n"
                "Each request should clearly describe the resource needed "
                "so suitable donations can be identified."
            ),
            "category": "receiver",
        },

        # =====================================================
        # MATCHING
        # =====================================================

        {
            "patterns": [
                r"\bwhat is matching\b",
                r"\bwhat does matching mean\b",
                r"\bsecondlife matching\b",
            ],
            "answer": (
                "Matching is the process of connecting available donations "
                "with receiver requests that may be suitable for those items.\n\n"
                "The goal is to help useful resources reach people or "
                "organizations that can benefit from them."
            ),
            "category": "matching",
        },

        {
            "patterns": [
                r"\bhow does matching work\b",
                r"\bhow are donations matched\b",
                r"\bhow are donors matched\b",
                r"\bhow are receivers matched\b",
                r"\bhow do you match donations\b",
            ],
            "answer": (
                "SecondLife's matching process helps identify suitable "
                "connections between donated items and receiver requests.\n\n"
                "Relevant information can include item category, requirements, "
                "availability, and other details provided through the platform."
            ),
            "category": "matching",
        },

        {
            "patterns": [
                r"\bwhat happens after matching\b",
                r"\bafter a match\b",
                r"\bwhat happens when donation is matched\b",
                r"\bwhat happens after a donation is matched\b",
            ],
            "answer": (
                "After a suitable match is identified, the connection can "
                "move toward the handover and delivery stage.\n\n"
                "The exact process depends on the information available "
                "and the platform's current workflow."
            ),
            "category": "matching",
        },

        {
            "patterns": [
                r"\bcan matching fail\b",
                r"\bwhat if there is no match\b",
                r"\bno matching donation\b",
                r"\bwhy is my request not matched\b",
            ],
            "answer": (
                "A request may not immediately find a suitable match if "
                "there is no compatible donation currently available.\n\n"
                "Keeping request information accurate and up to date can "
                "help improve the possibility of finding a suitable resource."
            ),
            "category": "matching",
        },

        # =====================================================
        # CONNECTIONS
        # =====================================================

        {
            "patterns": [
                r"\bwhat are connections\b",
                r"\bwhat is a connection\b",
                r"\bsecondlife connections\b",
            ],
            "answer": (
                "A connection represents the relationship established "
                "between a donor offering an item and a receiver who needs it.\n\n"
                "Connections help move successful matches toward the "
                "handover stage."
            ),
            "category": "connections",
        },

        {
            "patterns": [
                r"\bhow do connections work\b",
                r"\bhow does connection work\b",
                r"\bconnect donor and receiver\b",
            ],
            "answer": (
                "Once a suitable donation and receiver request are identified, "
                "SecondLife can establish a connection between the relevant parties.\n\n"
                "This helps coordinate the next stage of the resource-sharing process."
            ),
            "category": "connections",
        },

        # =====================================================
        # DELIVERY / HANDOVER
        # =====================================================

        {
            "patterns": [
                r"\bhow does delivery work\b",
                r"\bhow are donations delivered\b",
                r"\bhow do items get delivered\b",
                r"\bdelivery process\b",
            ],
            "answer": (
                "After a suitable donor-receiver connection is established, "
                "the parties can proceed toward the item's handover or delivery.\n\n"
                "Delivery arrangements may depend on the item's size, location, "
                "availability, and arrangements made by the relevant parties."
            ),
            "category": "delivery",
        },

        {
            "patterns": [
                r"\bwho delivers the item\b",
                r"\bwho will deliver\b",
                r"\bdelivery responsibility\b",
            ],
            "answer": (
                "Delivery responsibility depends on the specific donation "
                "and the arrangements between the relevant parties.\n\n"
                "SecondLife's role is to facilitate the digital connection "
                "and resource-sharing process."
            ),
            "category": "delivery",
        },

        {
            "patterns": [
                r"\bis delivery free\b",
                r"\bdelivery cost\b",
                r"\bwho pays delivery\b",
                r"\bshipping cost\b",
            ],
            "answer": (
                "SecondLife follows a zero-fee digital handover model.\n\n"
                "Any physical transportation or delivery arrangements may "
                "depend on the specific donor, receiver, location, and item."
            ),
            "category": "delivery",
        },

        # =====================================================
        # REGISTRATION
        # =====================================================

        {
            "patterns": [
                r"\bhow do i register\b",
                r"\bhow can i register\b",
                r"\bhow to register\b",
                r"\bregistration process\b",
                r"\bhow do i create an account\b",
                r"\bcreate account\b",
            ],
            "answer": (
                "Registration begins by selecting the appropriate account "
                "type and completing the required information.\n\n"
                "Depending on your role, you can register as a Donor or "
                "Receiver and select the relevant Individual or Organization "
                "option where available."
            ),
            "category": "registration",
        },

        {
            "patterns": [
                r"\bwhat account types are available\b",
                r"\baccount types\b",
                r"\btypes of accounts\b",
                r"\bindividual or organization\b",
            ],
            "answer": (
                "SecondLife provides account options designed for different "
                "participants in the resource-sharing ecosystem.\n\n"
                "Users can participate as Donors or Receivers, with Individual "
                "and Organization registration options where applicable."
            ),
            "category": "registration",
        },

        {
            "patterns": [
                r"\bcan i register as an individual\b",
                r"\bindividual registration\b",
                r"\bindividual account\b",
            ],
            "answer": (
                "Yes. Individuals can register on SecondLife by selecting "
                "the Individual option and completing the required registration details."
            ),
            "category": "registration",
        },

        {
            "patterns": [
                r"\bcan organizations register\b",
                r"\borganization registration\b",
                r"\bregister organization\b",
                r"\borganization account\b",
            ],
            "answer": (
                "Yes. Organizations can register on SecondLife where the "
                "organization account option is available.\n\n"
                "Organization registration may require information such as "
                "the organization name, contact details, license or registration "
                "number, and other required information."
            ),
            "category": "registration",
        },

        {
            "patterns": [
                r"\bwhat information is required for registration\b",
                r"\bwhat do i need to register\b",
                r"\bregistration requirements\b",
                r"\bwhat information do i need\b",
            ],
            "answer": (
                "Registration requirements depend on the selected account type.\n\n"
                "Users should provide accurate identity, contact, and account "
                "information requested by the registration form. Organizations "
                "may also be asked for registration or license information."
            ),
            "category": "registration",
        },

        # =====================================================
        # ORGANIZATIONS
        # =====================================================

        {
            "patterns": [
                r"\bcan organizations donate\b",
                r"\bcan companies donate\b",
                r"\bcan businesses donate\b",
                r"\borganization donation\b",
            ],
            "answer": (
                "Yes. Organizations can contribute useful resources through "
                "SecondLife where organization donor accounts are supported.\n\n"
                "This allows businesses and organizations to redirect useful "
                "surplus items toward people or communities that may need them."
            ),
            "category": "organization",
        },

        {
            "patterns": [
                r"\bcan organizations receive\b",
                r"\bcan ngos receive donations\b",
                r"\borganization receiver\b",
                r"\bcan an organization receive\b",
            ],
            "answer": (
                "Eligible organizations can participate as receivers where "
                "organization accounts are supported.\n\n"
                "They can request useful resources relevant to their needs."
            ),
            "category": "organization",
        },

        {
            "patterns": [
                r"\bwhy should organizations use secondlife\b",
                r"\bbenefits for organizations\b",
                r"\bsecondlife for organizations\b",
            ],
            "answer": (
                "SecondLife can provide organizations with a structured way "
                "to share surplus resources or request useful items.\n\n"
                "It supports a more organized approach to resource sharing "
                "while encouraging reuse and community impact."
            ),
            "category": "organization",
        },

        # =====================================================
        # SAFETY
        # =====================================================

        {
            "patterns": [
                r"\bis secondlife safe\b",
                r"\bis secondlife secure\b",
                r"\bsafety of secondlife\b",
                r"\bis donation safe\b",
            ],
            "answer": (
                "Safety and responsible resource sharing are important "
                "principles of SecondLife.\n\n"
                "Users should provide accurate information, avoid sharing "
                "unnecessary sensitive information, and only participate "
                "in safe and appropriate handovers."
            ),
            "category": "safety",
        },

        {
            "patterns": [
                r"\bwhat should i do if i see suspicious activity\b",
                r"\bhow do i report suspicious activity\b",
                r"\breport suspicious user\b",
                r"\breport a problem\b",
            ],
            "answer": (
                "If you encounter suspicious activity, inaccurate information, "
                "or an unsafe situation, use the platform's available reporting "
                "or support mechanism.\n\n"
                "Do not share passwords, verification codes, or other sensitive "
                "credentials with another user."
            ),
            "category": "safety",
        },

        {
            "patterns": [
                r"\bshould i share my password\b",
                r"\bcan i share my password\b",
                r"\bshare login credentials\b",
                r"\bshare verification code\b",
            ],
            "answer": (
                "No. Never share your password, verification codes, or other "
                "authentication credentials with another person.\n\n"
                "Keep your account information private and use only official "
                "platform mechanisms for account support."
            ),
            "category": "safety",
        },

        # =====================================================
        # ZERO FEE / COST
        # =====================================================

        {
            "patterns": [
                r"\bis secondlife free\b",
                r"\bis secondlife zero fee\b",
                r"\bdo i have to pay\b",
                r"\bdoes secondlife charge money\b",
                r"\bis there a fee\b",
                r"\bdoes it cost money\b",
            ],
            "answer": (
                "SecondLife is designed around transparent, zero-fee "
                "digital handovers for the resource-sharing process.\n\n"
                "The platform's purpose is to facilitate the sharing "
                "of useful items rather than commercial sales."
            ),
            "category": "general",
        },

        # =====================================================
        # ENVIRONMENT
        # =====================================================

        {
            "patterns": [
                r"\bhow does secondlife help environment\b",
                r"\benvironmental impact\b",
                r"\bdoes secondlife reduce waste\b",
                r"\bhow does secondlife reduce waste\b",
            ],
            "answer": (
                "SecondLife supports environmental sustainability by "
                "encouraging reuse instead of unnecessary disposal.\n\n"
                "When useful products remain in circulation for longer, "
                "their lifecycles can be extended and unnecessary waste "
                "can be reduced."
            ),
            "category": "impact",
        },

        {
            "patterns": [
                r"\bwhat is circular resource sharing\b",
                r"\bwhat is circular sharing\b",
                r"\bcircular resource\b",
                r"\bcircular economy\b",
            ],
            "answer": (
                "Circular resource sharing focuses on keeping useful products "
                "and materials in use for as long as possible.\n\n"
                "SecondLife applies this principle by connecting unused but "
                "useful items with people and organizations that can benefit "
                "from them."
            ),
            "category": "impact",
        },

        # =====================================================
        # IMPACT
        # =====================================================

        {
            "patterns": [
                r"\bwhat is the impact of secondlife\b",
                r"\bsecondlife impact\b",
                r"\bhow does secondlife create impact\b",
            ],
            "answer": (
                "SecondLife aims to create both social and environmental impact.\n\n"
                "Socially, it helps useful resources reach people and "
                "organizations that need them.\n\n"
                "Environmentally, it encourages reuse and helps extend "
                "product lifecycles."
            ),
            "category": "impact",
        },

        {
            "patterns": [
                r"\bhow does secondlife help communities\b",
                r"\bcommunity impact\b",
                r"\bhow does it help people\b",
            ],
            "answer": (
                "SecondLife helps communities by creating a structured way "
                "for people and organizations to share resources.\n\n"
                "Instead of allowing useful items to remain unused or become "
                "waste, the platform helps connect them with potential receivers."
            ),
            "category": "impact",
        },

        {
            "patterns": [
                r"\bwhy is reuse important\b",
                r"\bwhy reuse items\b",
                r"\bimportance of reuse\b",
            ],
            "answer": (
                "Reuse helps keep products useful for longer and can reduce "
                "unnecessary disposal.\n\n"
                "SecondLife promotes this principle by helping unused but "
                "useful items reach people and organizations that can use them."
            ),
            "category": "impact",
        },

        # =====================================================
        # PLATFORM FEATURES
        # =====================================================

        {
            "patterns": [
                r"\bwhat features does secondlife have\b",
                r"\bsecondlife features\b",
                r"\bfeatures of secondlife\b",
            ],
            "answer": (
                "SecondLife is designed around several core features:\n\n"
                "• Donor registration\n"
                "• Receiver registration\n"
                "• Individual and organization accounts\n"
                "• Donation listings\n"
                "• Receiver requests\n"
                "• Donation matching\n"
                "• Donor-receiver connections\n"
                "• Delivery and handover workflow\n"
                "• Administrative management\n"
                "• Community-focused resource sharing"
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bdoes secondlife have an admin panel\b",
                r"\bwhat does admin do\b",
                r"\bsecondlife admin\b",
                r"\badministrator\b",
                r"\badmin panel\b",
            ],
            "answer": (
                "The SecondLife administrative system is designed to help "
                "manage the platform's resource-sharing ecosystem.\n\n"
                "Administrative functions can include monitoring donors, "
                "receivers, donations, requests, matches, and connections."
            ),
            "category": "admin",
        },

        # =====================================================
        # ACCOUNT
        # =====================================================

        {
            "patterns": [
                r"\bhow do i login\b",
                r"\bhow do i log in\b",
                r"\bhow can i sign in\b",
                r"\blogin process\b",
                r"\bsign in process\b",
            ],
            "answer": (
                "Use the SecondLife login page and enter the credentials "
                "associated with your registered account.\n\n"
                "After successful authentication, you can access the "
                "dashboard associated with your account type."
            ),
            "category": "account",
        },

        {
            "patterns": [
                r"\bi forgot my password\b",
                r"\bforgot password\b",
                r"\breset password\b",
                r"\bpassword recovery\b",
            ],
            "answer": (
                "If you forget your password, use the password recovery "
                "or reset option provided on the login page.\n\n"
                "Follow the platform's instructions to regain access "
                "to your account."
            ),
            "category": "account",
        },

        {
            "patterns": [
                r"\bcan i change my account information\b",
                r"\bchange account information\b",
                r"\bedit profile\b",
                r"\bupdate profile\b",
            ],
            "answer": (
                "If profile editing is available in your dashboard, you "
                "can update the information supported by your account settings.\n\n"
                "Keep your profile information accurate so communication "
                "and resource sharing can remain organized."
            ),
            "category": "account",
        },

        # =====================================================
        # SUPPORT
        # =====================================================

        {
            "patterns": [
                r"\bhow can i contact secondlife\b",
                r"\bcontact secondlife\b",
                r"\bcontact support\b",
                r"\bsecondlife support\b",
                r"\bneed help\b",
                r"\bhow do i get help\b",
            ],
            "answer": (
                "For assistance with SecondLife, use the support or contact "
                "mechanism available through the platform.\n\n"
                "When reporting an issue, provide relevant details but "
                "never share your password or authentication credentials."
            ),
            "category": "support",
        },

        # =====================================================
        # CATEGORIES
        # =====================================================

        {
            "patterns": [
                r"\bwhat categories are available\b",
                r"\bavailable donation categories\b",
                r"\bdonation categories\b",
                r"\bwhich categories\b",
            ],
            "answer": (
                "The main SecondLife resource categories are:\n\n"
                "👕 Clothes\n"
                "📚 Books\n"
                "💻 Electronics\n"
                "🪑 Furniture\n"
                "🍱 Food\n\n"
                "These categories help organize donations and support "
                "the matching process."
            ),
            "category": "donation",
        },

        # =====================================================
        # FOUR-STAGE PROCESS
        # =====================================================

        {
            "patterns": [
                r"\bdonate match deliver impact\b",
                r"\bsecondlife four steps\b",
                r"\bfour steps of secondlife\b",
            ],
            "answer": (
                "Donate → Match → Deliver → Impact 🌿\n\n"
                "Donate: A user offers a useful item.\n"
                "Match: A suitable receiver can be identified.\n"
                "Deliver: The parties proceed toward handover or delivery.\n"
                "Impact: The item gets a second life and can benefit someone else."
            ),
            "category": "general",
        },

        # =====================================================
        # GREETINGS
        # =====================================================

        {
            "patterns": [
                r"^\bhi\b$",
                r"^\bhello\b$",
                r"^\bhey\b$",
                r"^\bhy\b$",
                r"^\bassalamualaikum\b$",
            ],
            "answer": (
                "Hello! 👋🌿\n\n"
                "I'm the SecondLife Assistant. I can help you understand "
                "donations, receivers, registration, matching, delivery, "
                "organizations, safety, and the SecondLife platform."
            ),
            "category": "general",
        },

        {
            "patterns": [
                r"\bthank you\b",
                r"\bthanks\b",
                r"\bthankyou\b",
                r"\bthx\b",
            ],
            "answer": (
                "You're welcome! 🌿\n\n"
                "I'm here to help you understand and use SecondLife."
            ),
            "category": "general",
        },
    ]

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize_text(text):
        text = str(text or "").lower().strip()

        # -----------------------------------------------------
        # SecondLife variations
        # -----------------------------------------------------

        text = text.replace("second-life", "secondlife")
        text = text.replace("second life", "secondlife")

        # -----------------------------------------------------
        # Common typing mistakes
        # -----------------------------------------------------

        replacements = {
            "donar": "donor",
            "doner": "donor",
            "donour": "donor",
            "reciever": "receiver",
            "recevier": "receiver",
            "reciver": "receiver",
            "registraton": "registration",
            "registation": "registration",
            "registeration": "registration",
            "donationn": "donation",
            "organizaton": "organization",
            "orgnization": "organization",
        }

        for old, new in replacements.items():
            text = re.sub(
                rf"\b{re.escape(old)}\b",
                new,
                text
            )

        # -----------------------------------------------------
        # Remove punctuation
        # -----------------------------------------------------

        text = re.sub(r"[^\w\s]", " ", text)

        # -----------------------------------------------------
        # Remove extra spaces
        # -----------------------------------------------------

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def get_words(text):
        return set(text.split())

    # =========================================================
    # DIRECT KNOWLEDGE BASE MATCH
    # =========================================================

    def get_knowledge_answer(self, user_message):
        message = self.normalize_text(user_message)

        for item in self.KNOWLEDGE_BASE:

            for pattern in item["patterns"]:

                if re.search(pattern, message):
                    return (
                        item["answer"],
                        item["category"]
                    )

        return None, None

    # =========================================================
    # FAQ SCORE
    # =========================================================

    def calculate_score(self, user_message, faq):

        message = self.normalize_text(user_message)
        question = self.normalize_text(faq.question)

        keywords = [
            self.normalize_text(keyword)
            for keyword in faq.keywords.split(",")
            if keyword.strip()
        ]

        score = 0

        # -----------------------------------------------------
        # Exact question
        # -----------------------------------------------------

        if message == question:
            score += 150

        # -----------------------------------------------------
        # Full question inside message
        # -----------------------------------------------------

        if question and question in message:
            score += 80

        # -----------------------------------------------------
        # Message inside FAQ question
        # -----------------------------------------------------

        if message and message in question:
            score += 60

        # -----------------------------------------------------
        # Keyword matching
        # -----------------------------------------------------

        for keyword in keywords:

            if not keyword:
                continue

            if keyword in message:

                score += 20

                if len(keyword.split()) > 1:
                    score += 15

        # -----------------------------------------------------
        # Meaningful word matching
        # -----------------------------------------------------

        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "how",
            "do",
            "does",
            "can",
            "i",
            "my",
            "me",
            "to",
            "of",
            "for",
            "and",
            "in",
            "on",
            "who",
            "are",
            "was",
            "it",
            "this",
            "that",
            "please",
            "tell",
            "you",
            "your",
            "about",
        }

        message_words = {
            word
            for word in self.get_words(message)
            if word not in stop_words
        }

        question_words = {
            word
            for word in self.get_words(question)
            if word not in stop_words
        }

        common_words = message_words.intersection(
            question_words
        )

        score += len(common_words) * 8

        # -----------------------------------------------------
        # Similarity
        # -----------------------------------------------------

        if message and question:

            similarity = SequenceMatcher(
                None,
                message,
                question
            ).ratio()

            if similarity >= 0.90:
                score += 60

            elif similarity >= 0.75:
                score += 40

            elif similarity >= 0.60:
                score += 20

        # -----------------------------------------------------
        # Admin priority
        # -----------------------------------------------------

        score += faq.priority

        return score

    # =========================================================
    # BEST FAQ
    # =========================================================

    def get_best_faq(self, user_message, faqs):

        best_faq = None
        best_score = 0

        for faq in faqs:

            score = self.calculate_score(
                user_message,
                faq
            )

            if score > best_score:

                best_score = score
                best_faq = faq

        return best_faq, best_score

    # =========================================================
    # SUGGESTIONS
    # =========================================================

    def get_suggestions(self, selected_faq=None):

        faqs = (
            ChatbotFAQ.objects
            .filter(is_active=True)
            .order_by("-priority")
        )

        suggestions = []

        for faq in faqs:

            if (
                selected_faq
                and faq.id == selected_faq.id
            ):
                continue

            if faq.question not in suggestions:

                suggestions.append(
                    faq.question
                )

            if len(suggestions) >= 5:
                break

        if not suggestions:
            return self.DEFAULT_SUGGESTIONS

        return suggestions

    # =========================================================
    # POST
    # =========================================================

    def post(self, request):
        try:
            return self._process_message(request)
        except Exception:
            return Response(
                {
                    "reply": self.DEFAULT_RESPONSE,
                    "suggestions": self.DEFAULT_SUGGESTIONS,
                    "category": "general",
                    "matched_question": None,
                    "confidence_score": 0,
                },
                status=status.HTTP_200_OK
            )

    def _process_message(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        user_message = str(
            data.get("message") or data.get("prompt") or data.get("query") or ""
        ).strip()

        # -----------------------------------------------------
        # Empty message
        # -----------------------------------------------------

        if not user_message:
            return Response(
                {
                    "error": "Message cannot be empty."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # DATABASE-DRIVEN INTENTS
        # =====================================================
        # Counts and available-item answers come from the live database.
        # This keeps the assistant from inventing current platform statistics.
        from django.contrib.auth import get_user_model
        from donations.models import Donation, Category
        User = get_user_model()
        normalized = user_message.lower()

        if any(k in normalized for k in ['how many donors', 'number of donors', 'total donors']):
            count = User.objects.filter(role='DONOR', is_active=True).count()
            return Response({'reply': f'There are currently {count} active donors on Second Life.', 'suggestions': self.DEFAULT_SUGGESTIONS, 'category': 'statistics'}, status=status.HTTP_200_OK)

        if any(k in normalized for k in ['how many receivers', 'number of receivers', 'total receivers']):
            count = User.objects.filter(role='RECEIVER', is_active=True).count()
            return Response({'reply': f'There are currently {count} active receivers on Second Life.', 'suggestions': self.DEFAULT_SUGGESTIONS, 'category': 'statistics'}, status=status.HTTP_200_OK)

        if 'how many' in normalized and 'categor' in normalized or 'number of categories' in normalized:
            count = Category.objects.count()
            return Response({'reply': f'Second Life currently has {count} donation categories.', 'suggestions': self.DEFAULT_SUGGESTIONS, 'category': 'statistics'}, status=status.HTTP_200_OK)

        if any(k in normalized for k in ['how many donations', 'number of donations', 'total donations']) and not any(k in normalized for k in ['available', 'active']):
            count = Donation.objects.count()
            return Response({'reply': f'There are currently {count} donations recorded on Second Life.', 'suggestions': self.DEFAULT_SUGGESTIONS, 'category': 'statistics'}, status=status.HTTP_200_OK)

        if any(k in normalized for k in ['available donations', 'active donations', 'what donations are available', "what's available", 'what is available']):
            available = Donation.objects.filter(status='AVAILABLE').order_by('-created_at')
            if 'how many' in normalized or 'number of' in normalized or 'count' in normalized:
                reply = f'There are currently {available.count()} available donations.'
            else:
                titles = list(available.values_list('title', flat=True)[:8])
                reply = ('Currently available donations include: ' + ', '.join(titles) + '.') if titles else 'There are no available donations right now.'
            return Response({'reply': reply, 'suggestions': self.DEFAULT_SUGGESTIONS, 'category': 'donations'}, status=status.HTTP_200_OK)

        # =====================================================
        # STEP 1
        # DIRECT KNOWLEDGE BASE
        # =====================================================

        knowledge_answer, knowledge_category = (
            self.get_knowledge_answer(
                user_message
            )
        )

        if knowledge_answer:

            return Response(
                {
                    "reply": knowledge_answer,

                    "suggestions": (
                        self.DEFAULT_SUGGESTIONS
                    ),

                    "category": (
                        knowledge_category
                    ),

                    "matched_question": None,
                },

                status=status.HTTP_200_OK
            )

        # =====================================================
        # STEP 2
        # DATABASE FAQ MATCHING
        # =====================================================

        faqs = (
            ChatbotFAQ.objects
            .filter(is_active=True)
        )

        best_faq, best_score = (
            self.get_best_faq(
                user_message,
                faqs
            )
        )

        # =====================================================
        # IMPORTANT:
        # Increased confidence threshold
        #
        # Old:
        # best_score >= 15
        #
        # New:
        # best_score >= 30
        # =====================================================

        if (
            best_faq
            and best_score >= 30
        ):

            return Response(
                {
                    "reply": best_faq.answer,

                    "suggestions": (
                        self.get_suggestions(
                            best_faq
                        )
                    ),

                    "category": (
                        best_faq.category
                    ),

                    "matched_question": (
                        best_faq.question
                    ),

                    "confidence_score": (
                        best_score
                    ),
                },

                status=status.HTTP_200_OK
            )

        # =====================================================
        # STEP 3
        # SAFE FALLBACK
        # =====================================================

        return Response(
            {
                "reply": self.DEFAULT_RESPONSE,

                "suggestions": (
                    self.DEFAULT_SUGGESTIONS
                ),

                "category": "general",

                "matched_question": None,

                "confidence_score": 0,
            },

            status=status.HTTP_200_OK
        )