from donations.models import Donation

class MatchingService:
    @staticmethod
    def calculate_match_score(donation: Donation, receiver_user) -> dict:
        """
        Rule-based matching algorithm that computes a compatibility score (0-100)
        between an available donation and a receiver profile.
        """
        score = 0
        match_factors = []

        # Category matching (High weight: 40 points)
        needed_cats = []
        if hasattr(receiver_user, 'profile') and receiver_user.profile.needed_categories:
            needed_cats = [c.lower() for c in receiver_user.profile.needed_categories]
        
        cat_name = donation.category.name.lower() if donation.category else ''
        cat_slug = donation.category.slug.lower() if donation.category else ''

        if any(cat in needed_cats for cat in [cat_name, cat_slug]):
            score += 40
            match_factors.append("Direct category match with needed items")
        else:
            # Baseline category availability
            score += 15
            match_factors.append("General category match")

        # Location matching (Medium weight: 30 points)
        receiver_city = (receiver_user.city or '').strip().lower()
        donation_city = (donation.city or '').strip().lower()

        if receiver_city and donation_city:
            if receiver_city == donation_city:
                score += 30
                match_factors.append(f"Located in same city ({donation.city})")
            else:
                score += 10
                match_factors.append("Within regional delivery network")
        else:
            score += 15

        # Condition preference (15 points)
        if donation.condition in ['NEW', 'LIKE_NEW']:
            score += 15
            match_factors.append(f"Prime condition ({donation.get_condition_display()})")
        elif donation.condition == 'GOOD':
            score += 12
            match_factors.append("Good usable condition")
        else:
            score += 8
            match_factors.append("Fair condition, functional")

        # Delivery / Logistics compatibility (15 points)
        receiver_pref = 'PICKUP'
        if hasattr(receiver_user, 'profile'):
            receiver_pref = receiver_user.profile.handover_preference

        if donation.delivery_option == 'EITHER' or receiver_pref == 'EITHER' or donation.delivery_option == receiver_pref:
            score += 15
            match_factors.append("Handover logistics fully compatible")
        else:
            score += 10
            match_factors.append("Pickup coordination required")

        final_score = min(100, max(0, score))
        return {
            'score': final_score,
            'percentage': f"{final_score}%",
            'is_recommended': final_score >= 70,
            'match_factors': match_factors
        }

    @classmethod
    def get_recommendations_for_receiver(cls, receiver_user, limit=6):
        """
        Returns recommended donations sorted by matching score for a given receiver.
        """
        available_donations = Donation.objects.filter(status='AVAILABLE').select_related('category', 'donor')
        scored_items = []

        for item in available_donations:
            match_info = cls.calculate_match_score(item, receiver_user)
            scored_items.append({
                'donation': item,
                'match_score': match_info['score'],
                'match_percentage': match_info['percentage'],
                'is_recommended': match_info['is_recommended'],
                'match_factors': match_info['match_factors'],
            })

        # Sort descending by score
        scored_items.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_items[:limit]
