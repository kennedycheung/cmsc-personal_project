"""Sample data used to populate a fresh database for local development and demos."""

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.airport import Airport
from app.models.destination import Destination

SAMPLE_DESTINATIONS: list[dict] = [
    {
        "name": "Banff National Park",
        "country": "Canada",
        "region": "North America",
        "description": "Alpine lakes, mountain hikes, and glacier viewpoints.",
        "budget_per_day": 220,
        "interests": "hiking,wildlife,scenery",
        "uniqueness_score": 7,
        "travel_difficulty": 4,
        "latitude": 51.4968,
        "longitude": -115.9281,
        "currency": "CAD",
        # Ski season (Dec-Mar) + summer (Jun-Aug) peaks; shoulder Apr-May/Sep-Nov cheapest.
        "seasonal_multipliers": "1.15,1.15,1.05,0.80,0.85,1.10,1.25,1.25,1.00,0.80,0.80,1.10",
        "activities": [
            {
                "name": "Lake Louise Canoe Tour", "category": "outdoor", "price": 45, "duration_hours": 2,
                "location": "Lake Louise", "opening_time": "08:00", "closing_time": "18:00", "travel_minutes": 25,
                "latitude": 51.4254, "longitude": -116.1773, "is_outdoor": True,
            },
            {
                "name": "Sulphur Mountain Gondola", "category": "sightseeing", "price": 60, "duration_hours": 3,
                "location": "Sulphur Mountain", "opening_time": "09:00", "closing_time": "21:00", "travel_minutes": 20,
                "latitude": 51.1517, "longitude": -115.5719, "is_outdoor": True,
            },
            {
                "name": "Johnston Canyon Icewalk", "category": "hiking", "price": 40, "duration_hours": 3,
                "location": "Johnston Canyon", "opening_time": "08:00", "closing_time": "17:00", "travel_minutes": 35,
                "latitude": 51.2371, "longitude": -115.8404, "is_outdoor": True,
            },
            {
                "name": "Banff Upper Hot Springs", "category": "relaxation", "price": 20, "duration_hours": 1.5,
                "location": "Sulphur Mountain Rd", "opening_time": "09:00", "closing_time": "22:00", "travel_minutes": 15,
                "latitude": 51.1633, "longitude": -115.5581, "is_outdoor": False,
            },
        ],
        "airports": [
            {
                "iata_code": "YYC", "name": "Calgary International", "distance_km": 130,
                "ground_transport_cost_usd": 60, "ground_transport_minutes": 90,
                "baseline_fare_usd": 450, "is_primary": True,
            },
            {
                "iata_code": "YEG", "name": "Edmonton International", "distance_km": 410,
                "ground_transport_cost_usd": 90, "ground_transport_minutes": 300,
                "baseline_fare_usd": 380, "is_primary": False,
            },
        ],
    },
    {
        "name": "Lisbon",
        "country": "Portugal",
        "region": "Europe",
        "description": "Historic neighborhoods, scenic coastlines, and local cuisine.",
        "budget_per_day": 140,
        "interests": "food,history,nightlife",
        "uniqueness_score": 5,
        "travel_difficulty": 2,
        "latitude": 38.7223,
        "longitude": -9.1393,
        "currency": "EUR",
        # Peak Jun-Aug, shoulder Apr-May/Sep-Oct, cheapest Nov-Mar.
        "seasonal_multipliers": "0.80,0.80,0.85,0.95,1.05,1.20,1.30,1.30,1.15,1.00,0.80,0.90",
        "activities": [
            {
                "name": "Tram 28 Historic Ride", "category": "sightseeing", "price": 15, "duration_hours": 1.5,
                "location": "Graça", "opening_time": "07:00", "closing_time": "21:00", "travel_minutes": 10,
                "latitude": 38.7139, "longitude": -9.1307, "is_outdoor": True,
            },
            {
                "name": "Fado Night & Dinner", "category": "food", "price": 55, "duration_hours": 3,
                "location": "Alfama", "opening_time": "19:00", "closing_time": "23:30", "travel_minutes": 15,
                "latitude": 38.7130, "longitude": -9.1290, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Sedona",
        "country": "United States",
        "region": "North America",
        "description": "Red rock trails, relaxing spas, and desert vistas.",
        "budget_per_day": 160,
        "interests": "hiking,relaxation,scenery",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 34.8697,
        "longitude": -111.7610,
        "currency": "USD",
        # Peak spring (Mar-May) + fall (Sep-Nov); brutal summer heat is cheapest.
        "seasonal_multipliers": "0.90,0.95,1.15,1.20,1.10,0.85,0.75,0.75,1.05,1.20,1.05,0.90",
        "activities": [
            {
                "name": "Red Rock Jeep Tour", "category": "adventure", "price": 95, "duration_hours": 3,
                "location": "Red Rock State Park", "opening_time": "08:00", "closing_time": "17:00", "travel_minutes": 20,
                "latitude": 34.8236, "longitude": -111.7990, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Chiang Mai",
        "country": "Thailand",
        "region": "Asia",
        "description": "Culture-rich markets, temples, and jungle adventures.",
        "budget_per_day": 70,
        "interests": "culture,food,trekking",
        "uniqueness_score": 6,
        "travel_difficulty": 5,
        "latitude": 18.7883,
        "longitude": 98.9853,
        "currency": "THB",
        # Cool dry season (Nov-Feb) peak; hot + rainy season (Mar-Oct) cheaper.
        "seasonal_multipliers": "1.20,1.15,0.90,0.85,0.80,0.80,0.80,0.80,0.80,0.85,1.05,1.20",
        "activities": [
            {
                "name": "Elephant Sanctuary Visit", "category": "wildlife", "price": 60, "duration_hours": 4,
                "location": "Mae Taeng", "opening_time": "08:00", "closing_time": "15:00", "travel_minutes": 60,
                "latitude": 19.0450, "longitude": 98.9200, "is_outdoor": True,
            },
            {
                "name": "Night Bazaar Food Tour", "category": "food", "price": 25, "duration_hours": 2,
                "location": "Night Bazaar", "opening_time": "18:00", "closing_time": "23:00", "travel_minutes": 15,
                "latitude": 18.7877, "longitude": 98.9930, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Napa Valley",
        "country": "United States",
        "region": "North America",
        "description": "Wine tastings, scenic vineyards, and slow-paced escapes.",
        "budget_per_day": 260,
        "interests": "food,wine,relaxation",
        "uniqueness_score": 5,
        "travel_difficulty": 2,
        "latitude": 38.2975,
        "longitude": -122.2869,
        "currency": "USD",
        # Harvest season (Sep-Oct) peak; winter (Dec-Feb) cheapest.
        "seasonal_multipliers": "0.80,0.85,0.90,1.00,1.05,1.15,1.20,1.15,1.30,1.30,0.95,0.85",
        "activities": [
            {
                "name": "Vineyard Tasting Tour", "category": "food", "price": 120, "duration_hours": 4,
                "location": "Silverado Trail", "opening_time": "10:00", "closing_time": "17:00", "travel_minutes": 25,
                "latitude": 38.4405, "longitude": -122.3389, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Kyoto",
        "country": "Japan",
        "region": "Asia",
        "description": "Historic temples, seasonal gardens, and refined food culture.",
        "budget_per_day": 180,
        "interests": "culture,history,food",
        "uniqueness_score": 8,
        "travel_difficulty": 3,
        "latitude": 35.0116,
        "longitude": 135.7681,
        "currency": "JPY",
        # Cherry blossom (Apr) and fall foliage (Nov) are sharp peaks; humid summer cheapest.
        "seasonal_multipliers": "0.90,0.90,1.10,1.35,1.05,0.90,0.85,0.85,0.95,1.10,1.30,0.95",
        "activities": [
            {
                "name": "Fushimi Inari Walking Tour", "category": "culture", "price": 20, "duration_hours": 3,
                "location": "Fushimi Inari Taisha", "opening_time": "05:00", "closing_time": "20:00", "travel_minutes": 30,
                "latitude": 34.9671, "longitude": 135.7727, "is_outdoor": True,
            },
            {
                "name": "Tea Ceremony Experience", "category": "culture", "price": 40, "duration_hours": 1.5,
                "location": "Gion", "opening_time": "10:00", "closing_time": "16:00", "travel_minutes": 15,
                "latitude": 35.0037, "longitude": 135.7788, "is_outdoor": False,
            },
            {
                "name": "Arashiyama Bamboo Grove Walk", "category": "scenery", "price": 0, "duration_hours": 1.5,
                "location": "Arashiyama", "opening_time": "07:00", "closing_time": "18:00", "travel_minutes": 40,
                "latitude": 35.0170, "longitude": 135.6717, "is_outdoor": True,
            },
            {
                "name": "Nishiki Market Food Crawl", "category": "food", "price": 35, "duration_hours": 2,
                "location": "Nishiki Market", "opening_time": "10:00", "closing_time": "18:00", "travel_minutes": 20,
                "latitude": 35.0050, "longitude": 135.7649, "is_outdoor": False,
            },
        ],
        "airports": [
            {
                "iata_code": "KIX", "name": "Kansai International", "distance_km": 55,
                "ground_transport_cost_usd": 25, "ground_transport_minutes": 75,
                "baseline_fare_usd": 700, "is_primary": True,
            },
            {
                "iata_code": "ITM", "name": "Osaka Itami", "distance_km": 55,
                "ground_transport_cost_usd": 20, "ground_transport_minutes": 60,
                "baseline_fare_usd": 650, "is_primary": False,
            },
            {
                "iata_code": "NGO", "name": "Chubu Centrair (Nagoya)", "distance_km": 145,
                "ground_transport_cost_usd": 40, "ground_transport_minutes": 150,
                "baseline_fare_usd": 600, "is_primary": False,
            },
        ],
    },
    {
        "name": "Reykjavik",
        "country": "Iceland",
        "region": "Europe",
        "description": "Volcanic landscapes, hot springs, and northern lights.",
        "budget_per_day": 240,
        "interests": "hiking,scenery,adventure",
        "uniqueness_score": 9,
        "travel_difficulty": 5,
        "latitude": 64.1466,
        "longitude": -21.9426,
        "currency": "ISK",
        # Midnight-sun summer (Jun-Aug) peak; shoulder Apr-May/Sep cheapest.
        "seasonal_multipliers": "0.90,0.90,0.85,0.80,0.85,1.25,1.35,1.30,0.90,0.85,0.85,0.95",
        "activities": [
            {
                "name": "Golden Circle Day Trip", "category": "adventure", "price": 140, "duration_hours": 8,
                "location": "Þingvellir", "opening_time": "08:00", "closing_time": "20:00", "travel_minutes": 10,
                "latitude": 64.2559, "longitude": -21.1295, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Marrakech",
        "country": "Morocco",
        "region": "Africa",
        "description": "Bustling souks, desert gateways, and vibrant riads.",
        "budget_per_day": 90,
        "interests": "culture,food,shopping",
        "uniqueness_score": 7,
        "travel_difficulty": 6,
        "latitude": 31.6295,
        "longitude": -7.9811,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "MAD",
        # Mild spring (Mar-May) + fall (Sep-Nov) peaks; brutal summer heat cheapest.
        "seasonal_multipliers": "0.95,1.00,1.15,1.20,1.10,0.85,0.75,0.75,1.00,1.15,1.10,1.00",
        "activities": [
            {
                "name": "Medina & Souks Walking Tour", "category": "culture", "price": 30, "duration_hours": 3,
                "location": "Medina", "opening_time": "09:00", "closing_time": "19:00", "travel_minutes": 10,
                "latitude": 31.6295, "longitude": -7.9811, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Queenstown",
        "country": "New Zealand",
        "region": "Oceania",
        "description": "Adrenaline capital with fjords, peaks, and lakes.",
        "budget_per_day": 200,
        "interests": "adventure,hiking,scenery",
        "uniqueness_score": 8,
        "travel_difficulty": 7,
        "latitude": -45.0312,
        "longitude": 168.6626,
        "currency": "NZD",
        # Southern Hemisphere: summer (Dec-Feb) + ski season (Jun-Aug) both peak.
        "seasonal_multipliers": "1.30,1.25,0.95,0.85,0.80,1.10,1.20,1.15,0.85,0.85,0.95,1.30",
        "activities": [
            {
                "name": "Bungee Jumping at Kawarau Bridge", "category": "adventure", "price": 180, "duration_hours": 1,
                "location": "Kawarau Bridge", "opening_time": "09:00", "closing_time": "17:00", "travel_minutes": 25,
                "latitude": -45.0392, "longitude": 168.7514, "is_outdoor": True,
            },
            {
                "name": "Milford Sound Cruise", "category": "scenery", "price": 150, "duration_hours": 6,
                "location": "Milford Sound", "opening_time": "08:00", "closing_time": "18:00", "travel_minutes": 90,
                "latitude": -44.6714, "longitude": 167.9252, "is_outdoor": True,
            },
            {
                "name": "Shotover Jet Boat Ride", "category": "adventure", "price": 130, "duration_hours": 1,
                "location": "Shotover River", "opening_time": "08:00", "closing_time": "17:00", "travel_minutes": 20,
                "latitude": -45.0089, "longitude": 168.6931, "is_outdoor": True,
            },
            {
                "name": "Queenstown Gondola & Luge", "category": "scenery", "price": 55, "duration_hours": 2,
                "location": "Bob's Peak", "opening_time": "09:00", "closing_time": "21:00", "travel_minutes": 10,
                "latitude": -45.0328, "longitude": 168.6746, "is_outdoor": True,
            },
        ],
        "airports": [
            {
                "iata_code": "ZQN", "name": "Queenstown Airport", "distance_km": 8,
                "ground_transport_cost_usd": 15, "ground_transport_minutes": 15,
                "baseline_fare_usd": 520, "is_primary": True,
            },
            {
                "iata_code": "CHC", "name": "Christchurch International", "distance_km": 485,
                "ground_transport_cost_usd": 70, "ground_transport_minutes": 360,
                "baseline_fare_usd": 390, "is_primary": False,
            },
        ],
    },
    {
        "name": "Bali",
        "country": "Indonesia",
        "region": "Asia",
        "description": "Rice terraces, temples, and laid-back beach towns.",
        "budget_per_day": 85,
        "interests": "relaxation,culture,surfing",
        "uniqueness_score": 6,
        "travel_difficulty": 4,
        "latitude": -8.5069,
        "longitude": 115.2625,
        "currency": "IDR",
        # Dry season (Jun-Sep) + year-end holidays peak; rainy Nov-Mar cheaper.
        "seasonal_multipliers": "1.05,0.95,0.90,0.95,1.05,1.20,1.30,1.30,1.15,0.95,0.85,1.20",
        "activities": [
            {
                "name": "Ubud Rice Terrace Trek", "category": "hiking", "price": 35, "duration_hours": 3,
                "location": "Tegallalang", "opening_time": "07:00", "closing_time": "17:00", "travel_minutes": 30,
                "latitude": -8.4310, "longitude": 115.2788, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Patagonia",
        "country": "Argentina",
        "region": "South America",
        "description": "Remote glaciers, granite peaks, and multi-day treks.",
        "budget_per_day": 150,
        "interests": "hiking,adventure,scenery",
        "uniqueness_score": 9,
        "travel_difficulty": 8,
        "latitude": -50.3379,
        "longitude": -72.2648,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "ARS",
        # Southern Hemisphere summer trekking season (Dec-Feb) peak; winter (May-Aug) very quiet.
        "seasonal_multipliers": "1.35,1.30,1.05,0.80,0.65,0.60,0.60,0.65,0.80,1.00,1.15,1.30",
        "activities": [
            {
                "name": "Torres del Paine Day Trek", "category": "hiking", "price": 150, "duration_hours": 8,
                "location": "Torres del Paine National Park", "opening_time": "06:00", "closing_time": "20:00",
                "travel_minutes": 60, "latitude": -50.9423, "longitude": -72.9963, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Prague",
        "country": "Czech Republic",
        "region": "Europe",
        "description": "Gothic spires, cobblestone lanes, and lively beer halls.",
        "budget_per_day": 110,
        "interests": "history,nightlife,culture",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 50.0755,
        "longitude": 14.4378,
        "currency": "CZK",
        # Christmas markets (Dec) + summer (Jun-Aug) peak; Jan-Mar cheapest.
        "seasonal_multipliers": "0.80,0.80,0.90,1.05,1.10,1.20,1.25,1.25,1.10,1.00,0.90,1.15",
        "activities": [
            {
                "name": "Old Town Walking Tour", "category": "history", "price": 20, "duration_hours": 2,
                "location": "Old Town Square", "opening_time": "09:00", "closing_time": "18:00", "travel_minutes": 10,
                "latitude": 50.0875, "longitude": 14.4213, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Cape Town",
        "country": "South Africa",
        "region": "Africa",
        "description": "Coastal cliffs, vineyards, and Table Mountain views.",
        "budget_per_day": 130,
        "interests": "adventure,scenery,food",
        "uniqueness_score": 8,
        "travel_difficulty": 6,
        "latitude": -33.9249,
        "longitude": 18.4241,
        "currency": "ZAR",
        # Southern Hemisphere summer (Dec-Feb) peak; winter (Jun-Aug) cheapest and rainiest.
        "seasonal_multipliers": "1.30,1.30,1.05,0.90,0.80,0.75,0.75,0.80,0.90,1.00,1.15,1.35",
        "activities": [
            {
                "name": "Table Mountain Cable Car", "category": "scenery", "price": 35, "duration_hours": 2,
                "location": "Table Mountain", "opening_time": "08:00", "closing_time": "18:00", "travel_minutes": 20,
                "latitude": -33.9628, "longitude": 18.4098, "is_outdoor": True,
            },
            {
                "name": "Shark Cage Diving", "category": "adventure", "price": 220, "duration_hours": 5,
                "location": "Gansbaai", "opening_time": "06:00", "closing_time": "12:00", "travel_minutes": 120,
                "latitude": -34.5833, "longitude": 19.3500, "is_outdoor": True,
            },
            {
                "name": "Boulders Beach Penguin Colony", "category": "wildlife", "price": 15, "duration_hours": 1.5,
                "location": "Simon's Town", "opening_time": "08:00", "closing_time": "17:30", "travel_minutes": 45,
                "latitude": -34.1938, "longitude": 18.4497, "is_outdoor": True,
            },
            {
                "name": "Cape Winelands Tasting Tour", "category": "food", "price": 70, "duration_hours": 4,
                "location": "Stellenbosch", "opening_time": "10:00", "closing_time": "17:00", "travel_minutes": 50,
                "latitude": -33.9321, "longitude": 18.8602, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Ho Chi Minh City",
        "country": "Vietnam",
        "region": "Asia",
        "description": "Street food alleys, war history, and buzzing markets.",
        "budget_per_day": 55,
        "interests": "food,culture,nightlife",
        "uniqueness_score": 5,
        "travel_difficulty": 4,
        "latitude": 10.7769,
        "longitude": 106.7009,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "VND",
        # Dry season (Dec-Apr) peak/comfortable; wet season (May-Nov) cheaper.
        "seasonal_multipliers": "1.15,1.15,1.10,1.05,0.90,0.85,0.85,0.85,0.85,0.90,0.95,1.10",
        "activities": [
            {
                "name": "Street Food Motorbike Tour", "category": "food", "price": 45, "duration_hours": 3,
                "location": "District 1", "opening_time": "18:00", "closing_time": "22:00", "travel_minutes": 15,
                "latitude": 10.7769, "longitude": 106.7009, "is_outdoor": True,
            },
        ],
    },
]


def seed_sample_data(db: Session) -> None:
    """Insert the sample dataset if the destinations table is currently empty."""
    if db.query(Destination).first() is not None:
        return

    for raw_entry in SAMPLE_DESTINATIONS:
        entry = dict(raw_entry)
        activities_data = entry.pop("activities", [])
        airports_data = entry.pop("airports", [])
        destination = Destination(**entry)
        destination.activities = [Activity(**activity) for activity in activities_data]
        destination.airports = [Airport(**airport) for airport in airports_data]
        db.add(destination)

    db.commit()
