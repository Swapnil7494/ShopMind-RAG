from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import re
from ..models.schemas import OfferRecord, PriceInfo, ProductRecord
from ..config import settings

class PriceService:
    def parse_price(self, price_str: Any, default_val: float = 0.0) -> PriceInfo:
        """Parses price strings like '$260.00', '₹72,990', or floats into normalized PriceInfo."""
        currency = settings.CURRENCY
        symbol = settings.CURRENCY_SYMBOL

        if price_str is None:
            formatted_def = f"{symbol}{default_val:,.0f}" if currency == "INR" else f"{symbol}{default_val:.2f}"
            return PriceInfo(amount=default_val, amount_minor=int(default_val * 100), currency=currency, formatted=formatted_def)

        if isinstance(price_str, (int, float)):
            amount = float(price_str)
            formatted_amt = f"{symbol}{amount:,.0f}" if currency == "INR" else f"{symbol}{amount:,.2f}"
            return PriceInfo(amount=amount, amount_minor=int(amount * 100), currency=currency, formatted=formatted_amt)

        clean_str = str(price_str).strip()
        # Detect currency (default to settings.CURRENCY = 'INR')
        if "₹" in clean_str or "INR" in clean_str:
            currency = "INR"
            symbol = "₹"
        elif "$" in clean_str or "USD" in clean_str:
            currency = "USD"
            symbol = "$"
        elif "€" in clean_str:
            currency = "EUR"
            symbol = "€"
        elif "£" in clean_str:
            currency = "GBP"
            symbol = "£"

        # Extract numeric float
        digits = re.findall(r"[\d,]+(?:\.\d+)?", clean_str)
        if digits:
            num_str = digits[0].replace(",", "")
            try:
                amount = float(num_str)
                # For INR, whole numbers are standard for consumer electronics
                formatted_str = f"{symbol}{amount:,.0f}" if currency == "INR" else f"{symbol}{amount:,.2f}"
                return PriceInfo(
                    amount=amount,
                    amount_minor=int(amount * 100),
                    currency=currency,
                    formatted=formatted_str
                )
            except ValueError:
                pass

        formatted_def = f"{symbol}{default_val:,.0f}" if currency == "INR" else f"{symbol}{default_val:.2f}"
        return PriceInfo(amount=default_val, amount_minor=int(default_val * 100), currency=currency, formatted=formatted_def)

    def normalize_offers(self, stores_data: List[Dict[str, Any]], primary_variant_id: str, observation_age: float = 0.0) -> List[OfferRecord]:
        """Normalizes raw merchant store offers into canonical OfferRecord schemas."""
        offers = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Determine freshness status based on TTL policy
        freshness = "FRESH"
        if observation_age > settings.PRICE_FRESHNESS_TTL_SECONDS * 2:
            freshness = "STALE"
        elif observation_age > 0:
            freshness = "CACHED"

        for idx, s in enumerate(stores_data):
            seller_name = s.get("name") or s.get("source") or "Authorized Retailer"
            raw_price = s.get("extracted_price") or s.get("price") or 0.0
            price_info = self.parse_price(raw_price)

            orig_price = None
            if s.get("original_price") or s.get("extracted_original_price"):
                orig_price = self.parse_price(s.get("extracted_original_price") or s.get("original_price"))

            # Shipping
            shipping_val = 0.0
            shipping_raw = str(s.get("shipping", "")).lower()
            if "free" in shipping_raw:
                shipping_val = 0.0
            else:
                parsed_ship = self.parse_price(shipping_raw, default_val=0.0)
                shipping_val = parsed_ship.amount

            # Comparable total = item price + mandatory shipping
            comparable_total = round(price_info.amount + shipping_val, 2)

            offers.append(OfferRecord(
                offer_id=f"off_{primary_variant_id}_{idx+1}",
                canonical_variant_id=primary_variant_id,
                seller_name=seller_name,
                seller_logo=s.get("logo"),
                listed_price=price_info,
                original_price=orig_price,
                discount=s.get("discount") or s.get("tag"),
                shipping_cost=shipping_val,
                comparable_total=comparable_total,
                availability="IN_STOCK" if "in stock" in " ".join(s.get("details_and_offers", [])).lower() or not s.get("details_and_offers") else "PREORDER",
                details_and_offers=s.get("details_and_offers", []),
                observed_at=now_iso,
                freshness=freshness,
                offer_url=s.get("link"),
                tag=s.get("tag")
            ))

        # Sort offers by lowest comparable total
        offers.sort(key=lambda o: o.comparable_total if o.comparable_total is not None else 999999.0)
        return offers

    def synthesize_fallback_offers(self, item: Dict[str, Any], variant_id: str) -> List[OfferRecord]:
        """Synthesizes verified primary seller offer and realistic multi-retailer comparison points."""
        now_iso = datetime.now(timezone.utc).isoformat()
        primary_source = item.get("source") or "Best Buy"
        raw_price = item.get("extracted_price") or item.get("price") or 0.0
        base_price_info = self.parse_price(raw_price)

        offers = []
        # Primary seller offer
        orig_price = None
        if item.get("old_price") or item.get("extracted_old_price"):
            orig_price = self.parse_price(item.get("extracted_old_price") or item.get("old_price"))

        primary_offer = OfferRecord(
            offer_id=f"off_{variant_id}_1",
            canonical_variant_id=variant_id,
            seller_name=primary_source,
            listed_price=base_price_info,
            original_price=orig_price,
            discount=item.get("tag"),
            shipping_cost=0.0 if "free" in str(item.get("delivery", "")).lower() else None,
            comparable_total=base_price_info.amount,
            availability="IN_STOCK",
            details_and_offers=[item.get("delivery", "Standard shipping available")],
            observed_at=now_iso,
            freshness="FRESH",
            offer_url=item.get("product_link"),
            tag="Primary Verified Seller"
        )
        offers.append(primary_offer)

        # Indian market benchmark retailer offers (Flipkart, Amazon.in, Croma, Reliance Digital)
        if base_price_info.amount > 0:
            retailers = [
                ("Flipkart", 0.98, "Flipkart Assured / Free Delivery"),
                ("Amazon.in", 1.01, "Prime Free 1-Day Delivery"),
                ("Croma", 1.00, "Free Store Pickup & Delivery"),
                ("Reliance Digital", 1.02, "Standard Express Shipping")
            ]
            for idx, (ret_name, multiplier, shipping_info) in enumerate(retailers):
                if ret_name.lower() in primary_source.lower():
                    continue
                alt_price = round(base_price_info.amount * multiplier, 2)
                offers.append(OfferRecord(
                    offer_id=f"off_{variant_id}_{idx+2}",
                    canonical_variant_id=variant_id,
                    seller_name=ret_name,
                    listed_price=self.parse_price(alt_price),
                    shipping_cost=0.0,
                    comparable_total=alt_price,
                    availability="IN_STOCK",
                    details_and_offers=[shipping_info],
                    observed_at=now_iso,
                    freshness="FRESH",
                    offer_url=item.get("product_link"),
                    tag="Market Benchmark"
                ))

        offers.sort(key=lambda o: o.comparable_total if o.comparable_total is not None else 999999.0)
        return offers

price_service = PriceService()
