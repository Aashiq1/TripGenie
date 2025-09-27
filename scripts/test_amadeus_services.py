#!/usr/bin/env python3
"""
Quick manual test for Amadeus flight/hotel services.

Usage examples:
  python scripts/test_amadeus_services.py --origins LAX JFK BOS --dest BCN --days-out 60 67
  python scripts/test_amadeus_services.py --origins LAX --dest CDG --dep 2025-03-10 --ret 2025-03-16
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Ensure imports work when invoked from repo root
sys.path.insert(0, os.getcwd())

from app.services.amadeus_flights import get_flight_offers  # noqa: E402
from app.services.amadeus_hotels import get_hotel_offers  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Amadeus services (flights/hotels)")
    parser.add_argument("--origins", nargs="+", default=["LAX", "JFK", "BOS"], help="Origin IATA codes")
    parser.add_argument("--dest", default="BCN", help="Destination IATA/city code")
    parser.add_argument("--dep", default=None, help="Departure date YYYY-MM-DD")
    parser.add_argument("--ret", default=None, help="Return date YYYY-MM-DD")
    parser.add_argument("--days-out", nargs=2, type=int, default=[60, 67], metavar=("DEP_OFFSET", "RET_OFFSET"), help="Offsets (days from today) if dep/ret omitted")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults per search")
    parser.add_argument("--class", dest="travel_class", default="ECONOMY", choices=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], help="Travel class")
    parser.add_argument("--nonstop", action="store_true", help="Search nonstop only")
    # Relaxed mode controls (script-level only)
    parser.add_argument("--hotel-pref", dest="hotel_pref", default="budget", choices=["budget", "standard", "luxury"], help="Hotel preference band")
    parser.add_argument("--relaxed-retry", dest="relaxed_retry", action="store_true", help="Retry flights with minimal filters if no results")
    parser.add_argument("--no-relaxed-retry", dest="relaxed_retry", action="store_false", help="Disable relaxed retry")
    parser.set_defaults(relaxed_retry=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.dep and args.ret:
        dep = args.dep
        ret = args.ret
    else:
        dep = (datetime.now() + timedelta(days=int(args.days_out[0]))).strftime("%Y-%m-%d")
        ret = (datetime.now() + timedelta(days=int(args.days_out[1]))).strftime("%Y-%m-%d")

    print(f"Testing flights → {args.origins} -> {args.dest} on {dep}..{ret}\n")
    for origin in args.origins:
        try:
            offers = get_flight_offers(
                departure_city=origin,
                destination=args.dest,
                departure_date=dep,
                return_date=ret,
                num_adults=args.adults,
                travel_class=args.travel_class,
                nonstop_only=bool(args.nonstop),
            )
            got_list = isinstance(offers, list)
            got_any = bool(offers) if got_list else False
            if got_list:
                print(f"{origin}->{args.dest}: {len(offers)} flight offers")
                if got_any:
                    cheapest = min(offers, key=lambda x: x.get("total_price", float("inf")))
                    print(f"  Cheapest: ${cheapest.get('total_price')} {cheapest.get('airline')} stops={cheapest.get('stops')}")
                else:
                    print(f"{origin}->{args.dest}: 0 offers returned")
            else:
                print(f"{origin}->{args.dest}: {offers}")

            # Relaxed retry if nothing came back or an error dict was returned
            if args.relaxed_retry and (not got_list or not got_any):
                print(f"Retrying relaxed flight search for {origin}->{args.dest} (ECONOMY, connections allowed, 1 adult)...")
                offers_relaxed = get_flight_offers(
                    departure_city=origin,
                    destination=args.dest,
                    departure_date=dep,
                    return_date=ret,
                    num_adults=1,
                    travel_class="ECONOMY",
                    nonstop_only=False,
                )
                if isinstance(offers_relaxed, list):
                    print(f"{origin}->{args.dest} (relaxed): {len(offers_relaxed)} flight offers")
                    if offers_relaxed:
                        cheapest_r = min(offers_relaxed, key=lambda x: x.get("total_price", float("inf")))
                        print(f"  Cheapest: ${cheapest_r.get('total_price')} {cheapest_r.get('airline')} stops={cheapest_r.get('stops')}")
                else:
                    print(f"{origin}->{args.dest} (relaxed): {offers_relaxed}")
        except Exception as e:
            print(f"{origin}->{args.dest}: ERROR {e}")

    print(f"\nTesting hotels → dest={args.dest} on {dep}..{ret}")
    try:
        hotels = get_hotel_offers(
            city_code=args.dest,
            check_in_date=dep,
            check_out_date=ret,
            accommodation_preference=args.hotel_pref,
        )
        count = len(hotels) if hotels else 0
        print(f"Hotels found: {count}")
        if hotels:
            sample = hotels[0]
            print(f"  Sample: {sample.get('hotel_name')} rating={sample.get('hotel_rating')} at {sample.get('address')}")
    except Exception as e:
        print(f"Hotels ERROR {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


