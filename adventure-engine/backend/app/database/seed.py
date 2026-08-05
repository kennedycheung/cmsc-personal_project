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
    # --- Major US cities -----------------------------------------------------
    {
        "name": "New York City",
        "country": "United States",
        "region": "North America",
        "description": "Iconic skyline, world-class museums, and endless neighborhoods to explore.",
        "budget_per_day": 280,
        "interests": "culture,food,nightlife",
        "uniqueness_score": 8,
        "travel_difficulty": 2,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "currency": "USD",
        # Holiday season (Dec) + summer (Jun-Aug) peak; Jan-Feb quietest.
        "seasonal_multipliers": "0.85,0.85,0.90,1.00,1.05,1.15,1.20,1.15,1.05,1.00,0.95,1.20",
        "activities": [
            {
                "name": "Statue of Liberty & Ellis Island Tour", "category": "sightseeing", "price": 25, "duration_hours": 4,
                "location": "Battery Park", "opening_time": "08:30", "closing_time": "17:00", "travel_minutes": 20,
                "latitude": 40.6892, "longitude": -74.0445, "is_outdoor": True,
            },
            {
                "name": "Broadway Show", "category": "culture", "price": 120, "duration_hours": 3,
                "location": "Times Square", "opening_time": "19:00", "closing_time": "23:00", "travel_minutes": 15,
                "latitude": 40.7590, "longitude": -73.9845, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Los Angeles",
        "country": "United States",
        "region": "North America",
        "description": "Beaches, Hollywood glamour, and year-round sunshine.",
        "budget_per_day": 220,
        "interests": "beaches,culture,food",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 34.0522,
        "longitude": -118.2437,
        "currency": "USD",
        # Mild year-round; summer (Jun-Aug) still peaks for tourism.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.15,1.20,1.20,1.05,0.95,0.90,1.00",
        "activities": [
            {
                "name": "Griffith Observatory & Hollywood Sign Hike", "category": "hiking", "price": 0, "duration_hours": 2,
                "location": "Griffith Park", "opening_time": "10:00", "closing_time": "22:00", "travel_minutes": 25,
                "latitude": 34.1184, "longitude": -118.3004, "is_outdoor": True,
            },
            {
                "name": "Santa Monica Pier & Beach", "category": "relaxation", "price": 15, "duration_hours": 3,
                "location": "Santa Monica", "opening_time": "09:00", "closing_time": "23:00", "travel_minutes": 30,
                "latitude": 34.0092, "longitude": -118.4973, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Chicago",
        "country": "United States",
        "region": "North America",
        "description": "Lakefront skyline, deep-dish pizza, and world-class architecture.",
        "budget_per_day": 190,
        "interests": "architecture,food,culture",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 41.8781,
        "longitude": -87.6298,
        "currency": "USD",
        # Summer (Jun-Aug) peak; brutal winter (Jan-Feb) cheapest.
        "seasonal_multipliers": "0.85,0.85,0.90,1.00,1.05,1.15,1.20,1.15,1.05,0.95,0.85,1.15",
        "activities": [
            {
                "name": "Chicago Architecture River Cruise", "category": "sightseeing", "price": 50, "duration_hours": 1.5,
                "location": "Chicago River", "opening_time": "09:00", "closing_time": "19:00", "travel_minutes": 10,
                "latitude": 41.8875, "longitude": -87.6255, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "San Francisco",
        "country": "United States",
        "region": "North America",
        "description": "Fog-draped hills, the Golden Gate Bridge, and diverse neighborhoods.",
        "budget_per_day": 260,
        "interests": "scenery,food,culture",
        "uniqueness_score": 7,
        "travel_difficulty": 3,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "currency": "USD",
        # Mild year-round; Sep-Oct (Indian summer) is actually the sunniest stretch.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.10,1.10,1.10,1.10,1.00,0.90,1.05",
        "activities": [
            {
                "name": "Golden Gate Bridge & Presidio Bike Ride", "category": "outdoor", "price": 40, "duration_hours": 3,
                "location": "Presidio", "opening_time": "08:00", "closing_time": "18:00", "travel_minutes": 20,
                "latitude": 37.8199, "longitude": -122.4783, "is_outdoor": True,
            },
            {
                "name": "Alcatraz Island Tour", "category": "history", "price": 45, "duration_hours": 2.5,
                "location": "Pier 33", "opening_time": "09:00", "closing_time": "16:30", "travel_minutes": 15,
                "latitude": 37.8267, "longitude": -122.4230, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Las Vegas",
        "country": "United States",
        "region": "North America",
        "description": "Neon-lit casinos, extravagant shows, and desert day trips.",
        "budget_per_day": 210,
        "interests": "nightlife,casinos,adventure",
        "uniqueness_score": 8,
        "travel_difficulty": 2,
        "latitude": 36.1699,
        "longitude": -115.1398,
        "currency": "USD",
        # Mild spring/fall peak; brutal summer desert heat cheapest.
        "seasonal_multipliers": "1.15,1.15,1.20,1.15,0.95,0.75,0.70,0.70,0.90,1.10,1.15,1.20",
        "activities": [
            {
                "name": "Grand Canyon West Rim Day Trip", "category": "adventure", "price": 200, "duration_hours": 8,
                "location": "Grand Canyon West", "opening_time": "07:00", "closing_time": "19:00", "travel_minutes": 150,
                "latitude": 36.0847, "longitude": -113.8117, "is_outdoor": True,
            },
            {
                "name": "Cirque du Soleil Show", "category": "nightlife", "price": 130, "duration_hours": 2,
                "location": "The Strip", "opening_time": "19:00", "closing_time": "23:00", "travel_minutes": 10,
                "latitude": 36.1147, "longitude": -115.1728, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Miami",
        "country": "United States",
        "region": "North America",
        "description": "Art Deco beaches, Latin flavors, and nonstop nightlife.",
        "budget_per_day": 210,
        "interests": "beaches,nightlife,food",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 25.7617,
        "longitude": -80.1918,
        "currency": "USD",
        # Snowbird season (Dec-Apr) peak; hot, humid, hurricane-risk summer cheapest.
        "seasonal_multipliers": "1.25,1.25,1.20,1.10,0.95,0.80,0.80,0.80,0.75,0.90,1.05,1.25",
        "activities": [
            {
                "name": "South Beach & Ocean Drive", "category": "relaxation", "price": 0, "duration_hours": 3,
                "location": "South Beach", "opening_time": "06:00", "closing_time": "22:00", "travel_minutes": 15,
                "latitude": 25.7825, "longitude": -80.1300, "is_outdoor": True,
            },
            {
                "name": "Little Havana Food & Culture Tour", "category": "food", "price": 60, "duration_hours": 3,
                "location": "Calle Ocho", "opening_time": "11:00", "closing_time": "18:00", "travel_minutes": 20,
                "latitude": 25.7658, "longitude": -80.2192, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "New Orleans",
        "country": "United States",
        "region": "North America",
        "description": "Jazz-filled streets, Creole cuisine, and historic French architecture.",
        "budget_per_day": 170,
        "interests": "music,food,history",
        "uniqueness_score": 8,
        "travel_difficulty": 3,
        "latitude": 29.9511,
        "longitude": -90.0715,
        "currency": "USD",
        # Mardi Gras / spring (Feb-Apr) peak; hot, humid, hurricane-risk summer cheapest.
        "seasonal_multipliers": "1.25,1.25,1.20,1.10,0.95,0.75,0.75,0.75,0.75,0.90,1.05,1.30",
        "activities": [
            {
                "name": "French Quarter & Jazz Walking Tour", "category": "history", "price": 30, "duration_hours": 2.5,
                "location": "French Quarter", "opening_time": "10:00", "closing_time": "22:00", "travel_minutes": 10,
                "latitude": 29.9584, "longitude": -90.0644, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Seattle",
        "country": "United States",
        "region": "North America",
        "description": "Coffee culture, waterfront views, and gateway to the Pacific Northwest.",
        "budget_per_day": 200,
        "interests": "food,scenery,culture",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 47.6062,
        "longitude": -122.3321,
        "currency": "USD",
        # Dry, sunny summer (Jun-Aug) peak; rainy winter cheapest.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.20,1.25,1.20,1.05,0.95,0.90,1.00",
        "activities": [
            {
                "name": "Pike Place Market Food Tour", "category": "food", "price": 55, "duration_hours": 2.5,
                "location": "Pike Place Market", "opening_time": "09:00", "closing_time": "18:00", "travel_minutes": 10,
                "latitude": 47.6097, "longitude": -122.3422, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Austin",
        "country": "United States",
        "region": "North America",
        "description": "Live music, food trucks, and a laid-back Texas capital.",
        "budget_per_day": 170,
        "interests": "music,food,nightlife",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 30.2672,
        "longitude": -97.7431,
        "currency": "USD",
        # Spring (SXSW) and fall festival seasons peak; brutal summer heat quieter.
        "seasonal_multipliers": "0.90,0.90,1.00,1.10,1.10,1.00,0.90,0.90,1.05,1.10,0.95,1.00",
        "activities": [
            {
                "name": "Live Music on Rainey Street", "category": "nightlife", "price": 20, "duration_hours": 3,
                "location": "Rainey Street", "opening_time": "18:00", "closing_time": "23:59", "travel_minutes": 10,
                "latitude": 30.2586, "longitude": -97.7373, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Nashville",
        "country": "United States",
        "region": "North America",
        "description": "Honky-tonks, country music history, and Southern comfort food.",
        "budget_per_day": 180,
        "interests": "music,food,nightlife",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 36.1627,
        "longitude": -86.7816,
        "currency": "USD",
        # Spring and fall are the most popular weekend-trip seasons.
        "seasonal_multipliers": "0.90,0.90,1.00,1.10,1.10,1.00,0.90,0.90,1.05,1.10,0.95,1.05",
        "activities": [
            {
                "name": "Broadway Honky-Tonk Bar Crawl", "category": "nightlife", "price": 25, "duration_hours": 3,
                "location": "Lower Broadway", "opening_time": "17:00", "closing_time": "23:59", "travel_minutes": 10,
                "latitude": 36.1612, "longitude": -86.7775, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Washington, D.C.",
        "country": "United States",
        "region": "North America",
        "description": "Free world-class museums and the seat of American history.",
        "budget_per_day": 230,
        "interests": "history,culture,sightseeing",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 38.9072,
        "longitude": -77.0369,
        "currency": "USD",
        # Cherry blossom season (Apr) is a sharp peak; humid summer stays busy too.
        "seasonal_multipliers": "0.85,0.85,1.05,1.20,1.05,1.00,0.95,0.90,0.95,1.00,0.90,1.10",
        "activities": [
            {
                "name": "Smithsonian National Mall Walking Tour", "category": "history", "price": 0, "duration_hours": 4,
                "location": "National Mall", "opening_time": "08:00", "closing_time": "17:30", "travel_minutes": 10,
                "latitude": 38.8899, "longitude": -77.0091, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Boston",
        "country": "United States",
        "region": "North America",
        "description": "Colonial history, Ivy League energy, and a walkable waterfront.",
        "budget_per_day": 230,
        "interests": "history,culture,food",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 42.3601,
        "longitude": -71.0589,
        "currency": "USD",
        # Summer (Jun-Aug) and fall foliage (Sep-Oct) both peak.
        "seasonal_multipliers": "0.85,0.85,0.90,1.00,1.05,1.15,1.20,1.15,1.15,1.10,0.90,1.15",
        "activities": [
            {
                "name": "Freedom Trail Walking Tour", "category": "history", "price": 15, "duration_hours": 2.5,
                "location": "Boston Common", "opening_time": "09:00", "closing_time": "17:00", "travel_minutes": 10,
                "latitude": 42.3555, "longitude": -71.0655, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Denver",
        "country": "United States",
        "region": "North America",
        "description": "Mile-high energy and a gateway to the Rocky Mountains.",
        "budget_per_day": 180,
        "interests": "hiking,scenery,adventure",
        "uniqueness_score": 5,
        "travel_difficulty": 3,
        "latitude": 39.7392,
        "longitude": -104.9903,
        "currency": "USD",
        # Summer hiking season (Jun-Aug) and fall foliage (Sep) peak.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.15,1.20,1.15,1.20,1.10,0.90,0.95",
        "activities": [
            {
                "name": "Rocky Mountain National Park Day Trip", "category": "hiking", "price": 30, "duration_hours": 8,
                "location": "Rocky Mountain National Park", "opening_time": "07:00", "closing_time": "19:00",
                "travel_minutes": 90, "latitude": 40.3428, "longitude": -105.6836, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Portland",
        "country": "United States",
        "region": "North America",
        "description": "Indie coffeehouses, food carts, and easy access to waterfalls and forests.",
        "budget_per_day": 180,
        "interests": "food,scenery,culture",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 45.5152,
        "longitude": -122.6784,
        "currency": "USD",
        # Dry, sunny summer (Jun-Aug) peak; rainy winter cheapest.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.20,1.25,1.20,1.05,0.95,0.90,1.00",
        "activities": [
            {
                "name": "Columbia River Gorge & Multnomah Falls", "category": "hiking", "price": 0, "duration_hours": 4,
                "location": "Multnomah Falls", "opening_time": "07:00", "closing_time": "19:00", "travel_minutes": 45,
                "latitude": 45.5762, "longitude": -122.1158, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "San Diego",
        "country": "United States",
        "region": "North America",
        "description": "Perfect weather, beaches, and a laid-back border-town energy.",
        "budget_per_day": 210,
        "interests": "beaches,relaxation,wildlife",
        "uniqueness_score": 5,
        "travel_difficulty": 2,
        "latitude": 32.7157,
        "longitude": -117.1611,
        "currency": "USD",
        # Very mild year-round; summer (Jun-Aug) still peaks for tourism.
        "seasonal_multipliers": "0.95,0.95,0.95,1.00,1.00,1.10,1.15,1.15,1.05,0.95,0.90,1.00",
        "activities": [
            {
                "name": "San Diego Zoo Safari Park", "category": "wildlife", "price": 70, "duration_hours": 4,
                "location": "Balboa Park", "opening_time": "09:00", "closing_time": "17:00", "travel_minutes": 15,
                "latitude": 32.7353, "longitude": -117.1490, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Honolulu",
        "country": "United States",
        "region": "Oceania",
        "description": "Legendary surf breaks, volcanic peaks, and Hawaiian culture.",
        "budget_per_day": 250,
        "interests": "beaches,surfing,culture",
        "uniqueness_score": 8,
        "travel_difficulty": 4,
        "latitude": 21.3069,
        "longitude": -157.8583,
        "currency": "USD",
        # Winter mainland-escape season and summer both peak; fall is quietest.
        "seasonal_multipliers": "1.15,1.10,1.05,1.00,1.00,1.10,1.15,1.15,1.00,0.95,1.00,1.20",
        "activities": [
            {
                "name": "Diamond Head Crater Hike", "category": "hiking", "price": 5, "duration_hours": 2,
                "location": "Diamond Head State Monument", "opening_time": "06:00", "closing_time": "16:00", "travel_minutes": 20,
                "latitude": 21.2620, "longitude": -157.8058, "is_outdoor": True,
            },
            {
                "name": "Waikiki Surf Lesson", "category": "surfing", "price": 80, "duration_hours": 2,
                "location": "Waikiki Beach", "opening_time": "07:00", "closing_time": "18:00", "travel_minutes": 10,
                "latitude": 21.2765, "longitude": -157.8256, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Charleston",
        "country": "United States",
        "region": "North America",
        "description": "Antebellum architecture, horse-drawn carriages, and coastal Lowcountry cuisine.",
        "budget_per_day": 180,
        "interests": "history,food,scenery",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 32.7765,
        "longitude": -79.9311,
        "currency": "USD",
        # Mild spring (Mar-May) peak; hot, humid summer cheapest.
        "seasonal_multipliers": "1.15,1.15,1.15,1.10,0.95,0.85,0.85,0.85,0.85,0.95,1.00,1.15",
        "activities": [
            {
                "name": "Historic District Carriage Tour", "category": "history", "price": 30, "duration_hours": 1,
                "location": "Market Street", "opening_time": "09:00", "closing_time": "17:00", "travel_minutes": 5,
                "latitude": 32.7817, "longitude": -79.9298, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Santa Fe",
        "country": "United States",
        "region": "North America",
        "description": "Adobe architecture, high-desert art galleries, and Southwestern cuisine.",
        "budget_per_day": 170,
        "interests": "art,culture,food",
        "uniqueness_score": 7,
        "travel_difficulty": 3,
        "latitude": 35.6870,
        "longitude": -105.9378,
        "currency": "USD",
        # Mild spring/fall peaks; brutal high-desert summer sun and winter cold cheaper.
        "seasonal_multipliers": "0.95,0.95,1.10,1.15,1.10,0.90,0.80,0.80,1.05,1.15,1.00,1.00",
        "activities": [
            {
                "name": "Canyon Road Art Walk", "category": "art", "price": 0, "duration_hours": 2,
                "location": "Canyon Road", "opening_time": "10:00", "closing_time": "17:00", "travel_minutes": 10,
                "latitude": 35.6884, "longitude": -105.9483, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Jackson Hole",
        "country": "United States",
        "region": "North America",
        "description": "Gateway to Grand Teton and Yellowstone, with world-class skiing in winter.",
        "budget_per_day": 230,
        "interests": "hiking,wildlife,skiing",
        "uniqueness_score": 8,
        "travel_difficulty": 5,
        "latitude": 43.4799,
        "longitude": -110.7624,
        "currency": "USD",
        # Ski season (Dec-Mar) peak; shoulder Apr-May/Oct-Nov cheapest.
        "seasonal_multipliers": "1.35,1.30,1.20,0.85,0.75,0.95,1.05,1.00,0.85,0.75,0.90,1.40",
        "activities": [
            {
                "name": "Grand Teton National Park Wildlife Safari", "category": "wildlife", "price": 110, "duration_hours": 5,
                "location": "Grand Teton National Park", "opening_time": "06:00", "closing_time": "13:00", "travel_minutes": 30,
                "latitude": 43.7904, "longitude": -110.6818, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Orlando",
        "country": "United States",
        "region": "North America",
        "description": "Theme park capital of the world, with year-round family attractions.",
        "budget_per_day": 200,
        "interests": "theme-parks,adventure,food",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 28.5383,
        "longitude": -81.3792,
        "currency": "USD",
        # Holiday weeks (Dec) and spring break (Mar-Apr) peak; fall hurricane season quieter.
        "seasonal_multipliers": "1.20,1.10,1.15,1.10,0.90,0.95,1.00,0.90,0.80,0.90,1.10,1.30",
        "activities": [
            {
                "name": "Walt Disney World Magic Kingdom Day", "category": "theme-parks", "price": 130, "duration_hours": 10,
                "location": "Magic Kingdom", "opening_time": "09:00", "closing_time": "22:00", "travel_minutes": 30,
                "latitude": 28.4177, "longitude": -81.5812, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Key West",
        "country": "United States",
        "region": "North America",
        "description": "Sunset celebrations, coral reefs, and a laid-back island vibe at the end of the road.",
        "budget_per_day": 220,
        "interests": "beaches,relaxation,nightlife",
        "uniqueness_score": 7,
        "travel_difficulty": 4,
        "latitude": 24.5551,
        "longitude": -81.7800,
        "currency": "USD",
        # Snowbird season (Dec-Apr) peak; hot, hurricane-risk summer cheapest.
        "seasonal_multipliers": "1.25,1.20,1.20,1.10,0.95,0.80,0.80,0.80,0.75,0.90,1.05,1.30",
        "activities": [
            {
                "name": "Sunset Celebration at Mallory Square", "category": "relaxation", "price": 0, "duration_hours": 1.5,
                "location": "Mallory Square", "opening_time": "17:00", "closing_time": "20:00", "travel_minutes": 5,
                "latitude": 24.5601, "longitude": -81.8072, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Asheville",
        "country": "United States",
        "region": "North America",
        "description": "Blue Ridge Mountain views, craft breweries, and Gilded Age mansions.",
        "budget_per_day": 160,
        "interests": "hiking,food,scenery",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 35.5951,
        "longitude": -82.5515,
        "currency": "USD",
        # Fall foliage (Sep-Oct) is the sharpest peak; summer also busy.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.10,1.15,1.10,1.20,1.25,0.90,0.95",
        "activities": [
            {
                "name": "Blue Ridge Parkway Scenic Drive", "category": "scenery", "price": 0, "duration_hours": 4,
                "location": "Blue Ridge Parkway", "opening_time": "07:00", "closing_time": "19:00", "travel_minutes": 20,
                "latitude": 35.5138, "longitude": -82.5488, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Palm Springs",
        "country": "United States",
        "region": "North America",
        "description": "Midcentury-modern architecture, desert spas, and mountain backdrops.",
        "budget_per_day": 200,
        "interests": "relaxation,art,scenery",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 33.8303,
        "longitude": -116.5453,
        "currency": "USD",
        # Mild winter (Nov-Mar) peak; brutal summer desert heat cheapest.
        "seasonal_multipliers": "1.20,1.20,1.15,1.05,0.90,0.70,0.65,0.65,0.85,1.05,1.15,1.25",
        "activities": [
            {
                "name": "Palm Springs Aerial Tramway", "category": "scenery", "price": 30, "duration_hours": 3,
                "location": "Chino Canyon", "opening_time": "08:00", "closing_time": "20:00", "travel_minutes": 15,
                "latitude": 33.8303, "longitude": -116.6119, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Aspen",
        "country": "United States",
        "region": "North America",
        "description": "World-class ski slopes and a glamorous mountain-town summer scene.",
        "budget_per_day": 320,
        "interests": "skiing,hiking,relaxation",
        "uniqueness_score": 7,
        "travel_difficulty": 5,
        "latitude": 39.1911,
        "longitude": -106.8175,
        "currency": "USD",
        # Peak ski season (Dec-Mar) is dramatically more expensive than any other time.
        "seasonal_multipliers": "1.45,1.40,1.30,0.80,0.70,0.90,1.00,1.00,0.85,0.75,0.95,1.50",
        "activities": [
            {
                "name": "Aspen Mountain Ski Day", "category": "skiing", "price": 220, "duration_hours": 6,
                "location": "Aspen Mountain", "opening_time": "09:00", "closing_time": "16:00", "travel_minutes": 10,
                "latitude": 39.1867, "longitude": -106.8203, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Philadelphia",
        "country": "United States",
        "region": "North America",
        "description": "Revolutionary War history, cheesesteaks, and a rising arts scene.",
        "budget_per_day": 180,
        "interests": "history,food,culture",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 39.9526,
        "longitude": -75.1652,
        "currency": "USD",
        # Summer (Jun-Aug) and holiday season peak; late winter cheapest.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.10,1.10,1.10,1.05,1.00,0.90,1.10",
        "activities": [
            {
                "name": "Independence Hall & Liberty Bell Tour", "category": "history", "price": 0, "duration_hours": 2,
                "location": "Independence National Historical Park", "opening_time": "09:00", "closing_time": "17:00",
                "travel_minutes": 10, "latitude": 39.9496, "longitude": -75.1503, "is_outdoor": True,
            },
        ],
    },
    # --- Top international destinations for American travelers ---------------
    {
        "name": "Paris",
        "country": "France",
        "region": "Europe",
        "description": "Iconic landmarks, world-class art, and unmatched café culture.",
        "budget_per_day": 200,
        "interests": "art,history,food",
        "uniqueness_score": 8,
        "travel_difficulty": 2,
        "latitude": 48.8566,
        "longitude": 2.3522,
        "currency": "EUR",
        # Peak Jun-Aug, shoulder Apr-May/Sep-Oct, cheapest Nov-Feb.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.25,1.30,1.25,1.10,0.95,0.85,1.10",
        "activities": [
            {
                "name": "Eiffel Tower & Seine River Cruise", "category": "sightseeing", "price": 45, "duration_hours": 3,
                "location": "Champ de Mars", "opening_time": "09:00", "closing_time": "23:00", "travel_minutes": 15,
                "latitude": 48.8584, "longitude": 2.2945, "is_outdoor": True,
            },
            {
                "name": "Louvre Museum Guided Tour", "category": "art", "price": 25, "duration_hours": 3,
                "location": "Louvre Museum", "opening_time": "09:00", "closing_time": "18:00", "travel_minutes": 10,
                "latitude": 48.8606, "longitude": 2.3376, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "London",
        "country": "United Kingdom",
        "region": "Europe",
        "description": "Royal history, world-class theatre, and a melting pot of global cuisine.",
        "budget_per_day": 210,
        "interests": "history,culture,nightlife",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 51.5074,
        "longitude": -0.1278,
        "currency": "GBP",
        # Peak Jun-Aug, shoulder spring/fall, cheapest Jan-Feb.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.20,1.30,1.25,1.10,0.95,0.85,1.10",
        "activities": [
            {
                "name": "Tower of London & Crown Jewels", "category": "history", "price": 35, "duration_hours": 2.5,
                "location": "Tower Hill", "opening_time": "09:00", "closing_time": "17:30", "travel_minutes": 15,
                "latitude": 51.5081, "longitude": -0.0759, "is_outdoor": False,
            },
            {
                "name": "West End Theatre Show", "category": "culture", "price": 90, "duration_hours": 2.5,
                "location": "West End", "opening_time": "19:30", "closing_time": "22:30", "travel_minutes": 15,
                "latitude": 51.5125, "longitude": -0.1300, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Rome",
        "country": "Italy",
        "region": "Europe",
        "description": "Ancient ruins, Renaissance art, and unbeatable Italian food.",
        "budget_per_day": 150,
        "interests": "history,food,culture",
        "uniqueness_score": 8,
        "travel_difficulty": 3,
        "latitude": 41.9028,
        "longitude": 12.4964,
        "currency": "EUR",
        # Sharp Mediterranean summer (Jun-Aug) peak; Nov-Feb cheapest.
        "seasonal_multipliers": "0.75,0.75,0.85,0.95,1.10,1.30,1.40,1.35,1.15,0.95,0.80,0.85",
        "activities": [
            {
                "name": "Colosseum & Roman Forum Tour", "category": "history", "price": 30, "duration_hours": 3,
                "location": "Colosseum", "opening_time": "08:30", "closing_time": "19:15", "travel_minutes": 15,
                "latitude": 41.8902, "longitude": 12.4922, "is_outdoor": True,
            },
            {
                "name": "Vatican Museums & Sistine Chapel", "category": "art", "price": 35, "duration_hours": 3,
                "location": "Vatican City", "opening_time": "08:00", "closing_time": "18:00", "travel_minutes": 25,
                "latitude": 41.9065, "longitude": 12.4536, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Barcelona",
        "country": "Spain",
        "region": "Europe",
        "description": "Gaudí architecture, Mediterranean beaches, and vibrant tapas culture.",
        "budget_per_day": 140,
        "interests": "art,food,beaches",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 41.3851,
        "longitude": 2.1734,
        "currency": "EUR",
        # Sharp Mediterranean summer (Jun-Aug) peak; Nov-Feb cheapest.
        "seasonal_multipliers": "0.75,0.75,0.85,0.95,1.10,1.25,1.35,1.35,1.15,0.95,0.80,0.90",
        "activities": [
            {
                "name": "Sagrada Familia Guided Tour", "category": "art", "price": 30, "duration_hours": 2,
                "location": "Sagrada Familia", "opening_time": "09:00", "closing_time": "18:00", "travel_minutes": 15,
                "latitude": 41.4036, "longitude": 2.1744, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Amsterdam",
        "country": "Netherlands",
        "region": "Europe",
        "description": "Historic canals, world-class museums, and easygoing bike culture.",
        "budget_per_day": 180,
        "interests": "culture,art,nightlife",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 52.3676,
        "longitude": 4.9041,
        "currency": "EUR",
        # Peak Jun-Aug, shoulder spring/fall, cheapest Nov-Feb.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.25,1.30,1.25,1.10,0.95,0.85,1.05",
        "activities": [
            {
                "name": "Canal Ring Bike Tour", "category": "sightseeing", "price": 25, "duration_hours": 2.5,
                "location": "Amsterdam Canal Ring", "opening_time": "09:00", "closing_time": "19:00", "travel_minutes": 10,
                "latitude": 52.3676, "longitude": 4.8852, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Dublin",
        "country": "Ireland",
        "region": "Europe",
        "description": "Literary pubs, medieval castles, and famously warm Irish hospitality.",
        "budget_per_day": 170,
        "interests": "culture,nightlife,history",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 53.3498,
        "longitude": -6.2603,
        "currency": "EUR",
        # Peak Jun-Aug, shoulder spring/fall, cheapest Nov-Feb.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.20,1.25,1.20,1.05,0.95,0.85,1.05",
        "activities": [
            {
                "name": "Guinness Storehouse & Temple Bar Crawl", "category": "nightlife", "price": 35, "duration_hours": 3,
                "location": "Temple Bar", "opening_time": "17:00", "closing_time": "23:00", "travel_minutes": 10,
                "latitude": 53.3428, "longitude": -6.2674, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Athens",
        "country": "Greece",
        "region": "Europe",
        "description": "Ancient ruins overlooking the Aegean and a lively modern food scene.",
        "budget_per_day": 120,
        "interests": "history,food,culture",
        "uniqueness_score": 7,
        "travel_difficulty": 3,
        "latitude": 37.9838,
        "longitude": 23.7275,
        "currency": "EUR",
        # Sharp Mediterranean summer (Jun-Aug) peak; Nov-Feb cheapest.
        "seasonal_multipliers": "0.75,0.75,0.85,0.95,1.10,1.30,1.40,1.35,1.15,0.95,0.80,0.85",
        "activities": [
            {
                "name": "Acropolis & Parthenon Tour", "category": "history", "price": 20, "duration_hours": 3,
                "location": "Acropolis", "opening_time": "08:00", "closing_time": "20:00", "travel_minutes": 15,
                "latitude": 37.9715, "longitude": 23.7267, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Santorini",
        "country": "Greece",
        "region": "Europe",
        "description": "Whitewashed cliffside villages and legendary Aegean sunsets.",
        "budget_per_day": 200,
        "interests": "scenery,relaxation,food",
        "uniqueness_score": 9,
        "travel_difficulty": 4,
        "latitude": 36.3932,
        "longitude": 25.4615,
        "currency": "EUR",
        # Extremely seasonal island economy: sharp Jul-Aug peak, near-dormant in winter.
        "seasonal_multipliers": "0.70,0.70,0.80,0.95,1.15,1.35,1.50,1.45,1.15,0.90,0.75,0.80",
        "activities": [
            {
                "name": "Oia Sunset Walk & Wine Tasting", "category": "relaxation", "price": 50, "duration_hours": 3,
                "location": "Oia", "opening_time": "17:00", "closing_time": "21:00", "travel_minutes": 25,
                "latitude": 36.4614, "longitude": 25.3753, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Venice",
        "country": "Italy",
        "region": "Europe",
        "description": "Canal-laced streets, Renaissance palaces, and gondola rides at dusk.",
        "budget_per_day": 190,
        "interests": "history,art,scenery",
        "uniqueness_score": 9,
        "travel_difficulty": 3,
        "latitude": 45.4408,
        "longitude": 12.3155,
        "currency": "EUR",
        # Peak Jun-Aug plus Carnival (Feb); Nov-Jan quietest and prone to flooding.
        "seasonal_multipliers": "0.75,0.75,0.90,1.00,1.10,1.25,1.30,1.25,1.15,1.00,0.80,0.90",
        "activities": [
            {
                "name": "Gondola Ride Through the Canals", "category": "sightseeing", "price": 90, "duration_hours": 1,
                "location": "Grand Canal", "opening_time": "09:00", "closing_time": "19:00", "travel_minutes": 10,
                "latitude": 45.4342, "longitude": 12.3388, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Florence",
        "country": "Italy",
        "region": "Europe",
        "description": "Renaissance masterpieces, Tuscan countryside, and world-class leather markets.",
        "budget_per_day": 150,
        "interests": "art,history,food",
        "uniqueness_score": 7,
        "travel_difficulty": 2,
        "latitude": 43.7696,
        "longitude": 11.2558,
        "currency": "EUR",
        # Sharp Mediterranean summer (Jun-Aug) peak; Nov-Feb cheapest.
        "seasonal_multipliers": "0.75,0.75,0.85,0.95,1.10,1.25,1.30,1.25,1.15,0.95,0.80,0.85",
        "activities": [
            {
                "name": "Uffizi Gallery Guided Tour", "category": "art", "price": 35, "duration_hours": 2.5,
                "location": "Uffizi Gallery", "opening_time": "08:15", "closing_time": "18:30", "travel_minutes": 10,
                "latitude": 43.7678, "longitude": 11.2553, "is_outdoor": False,
            },
        ],
    },
    {
        "name": "Berlin",
        "country": "Germany",
        "region": "Europe",
        "description": "Cold War history, cutting-edge nightlife, and a thriving arts scene.",
        "budget_per_day": 140,
        "interests": "history,nightlife,art",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 52.5200,
        "longitude": 13.4050,
        "currency": "EUR",
        # Peak Jun-Aug, shoulder spring/fall, cheapest Nov-Feb.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.20,1.25,1.20,1.05,0.95,0.85,1.00",
        "activities": [
            {
                "name": "Berlin Wall & East Side Gallery Tour", "category": "history", "price": 15, "duration_hours": 2,
                "location": "East Side Gallery", "opening_time": "09:00", "closing_time": "19:00", "travel_minutes": 15,
                "latitude": 52.5050, "longitude": 13.4396, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Vienna",
        "country": "Austria",
        "region": "Europe",
        "description": "Imperial palaces, classical music heritage, and elegant coffeehouses.",
        "budget_per_day": 160,
        "interests": "history,culture,food",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 48.2082,
        "longitude": 16.3738,
        "currency": "EUR",
        # Peak Jun-Aug plus Christmas markets (Dec); Jan-Feb cheapest.
        "seasonal_multipliers": "0.80,0.80,0.90,1.00,1.10,1.20,1.25,1.20,1.05,0.95,0.85,1.10",
        "activities": [
            {
                "name": "Schönbrunn Palace Tour", "category": "history", "price": 25, "duration_hours": 2.5,
                "location": "Schönbrunn Palace", "opening_time": "08:00", "closing_time": "17:30", "travel_minutes": 20,
                "latitude": 48.1858, "longitude": 16.3122, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Cancun",
        "country": "Mexico",
        "region": "North America",
        "description": "White-sand beaches, turquoise water, and easy access to Mayan ruins.",
        "budget_per_day": 150,
        "interests": "beaches,relaxation,history",
        "uniqueness_score": 5,
        "travel_difficulty": 2,
        "latitude": 21.1619,
        "longitude": -86.8515,
        "currency": "MXN",
        # Dry season (Dec-Apr) peak; hurricane-risk wet season (Jun-Oct) cheapest.
        "seasonal_multipliers": "1.30,1.30,1.25,1.15,0.90,0.75,0.75,0.75,0.70,0.85,1.05,1.35",
        "activities": [
            {
                "name": "Chichen Itza Day Trip", "category": "history", "price": 90, "duration_hours": 8,
                "location": "Chichen Itza", "opening_time": "06:00", "closing_time": "18:00", "travel_minutes": 150,
                "latitude": 20.6843, "longitude": -88.5678, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Tulum",
        "country": "Mexico",
        "region": "North America",
        "description": "Cliffside Mayan ruins, cenotes, and boho-chic beach clubs.",
        "budget_per_day": 140,
        "interests": "beaches,history,relaxation",
        "uniqueness_score": 7,
        "travel_difficulty": 3,
        "latitude": 20.2114,
        "longitude": -87.4654,
        "currency": "MXN",
        # Dry season (Dec-Apr) peak; hurricane-risk wet season (Jun-Oct) cheapest.
        "seasonal_multipliers": "1.30,1.30,1.25,1.15,0.90,0.75,0.75,0.75,0.70,0.85,1.05,1.35",
        "activities": [
            {
                "name": "Tulum Ruins & Cenote Swim", "category": "history", "price": 40, "duration_hours": 4,
                "location": "Tulum Archaeological Site", "opening_time": "08:00", "closing_time": "17:00", "travel_minutes": 20,
                "latitude": 20.2145, "longitude": -87.4295, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Punta Cana",
        "country": "Dominican Republic",
        "region": "North America",
        "description": "All-inclusive resorts and miles of palm-lined Caribbean coastline.",
        "budget_per_day": 180,
        "interests": "beaches,relaxation,nightlife",
        "uniqueness_score": 5,
        "travel_difficulty": 3,
        "latitude": 18.5601,
        "longitude": -68.3725,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "DOP",
        # Dry season (Dec-Apr) peak; hurricane-risk wet season (Jun-Oct) cheapest.
        "seasonal_multipliers": "1.30,1.30,1.25,1.15,0.90,0.75,0.75,0.75,0.70,0.85,1.05,1.35",
        "activities": [
            {
                "name": "Catamaran Snorkeling Tour", "category": "relaxation", "price": 75, "duration_hours": 4,
                "location": "Bavaro Beach", "opening_time": "09:00", "closing_time": "14:00", "travel_minutes": 15,
                "latitude": 18.6892, "longitude": -68.4114, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Nassau",
        "country": "Bahamas",
        "region": "North America",
        "description": "Colonial forts, swimming-pig day trips, and turquoise harbor views.",
        "budget_per_day": 200,
        "interests": "beaches,relaxation,adventure",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 25.0343,
        "longitude": -77.3963,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "BSD",
        # Dry season (Dec-Apr) peak; hurricane-risk wet season (Jun-Oct) cheapest.
        "seasonal_multipliers": "1.25,1.25,1.20,1.10,0.90,0.80,0.80,0.80,0.70,0.85,1.05,1.30",
        "activities": [
            {
                "name": "Exuma Swimming Pigs Day Trip", "category": "adventure", "price": 250, "duration_hours": 8,
                "location": "Nassau Harbour", "opening_time": "07:00", "closing_time": "17:00", "travel_minutes": 30,
                "latitude": 25.0480, "longitude": -77.3554, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "San Juan",
        "country": "Puerto Rico",
        "region": "North America",
        "description": "Colorful colonial streets, historic forts, and lively Latin nightlife.",
        "budget_per_day": 160,
        "interests": "history,nightlife,beaches",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 18.4655,
        "longitude": -66.1057,
        "currency": "USD",
        # Dry season (Dec-Apr) peak; hurricane-risk wet season (Jun-Oct) cheapest.
        "seasonal_multipliers": "1.20,1.20,1.15,1.05,0.90,0.85,0.85,0.85,0.75,0.85,1.00,1.25",
        "activities": [
            {
                "name": "Old San Juan Walking Tour", "category": "history", "price": 20, "duration_hours": 2.5,
                "location": "Old San Juan", "opening_time": "09:00", "closing_time": "18:00", "travel_minutes": 10,
                "latitude": 18.4663, "longitude": -66.1177, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Vancouver",
        "country": "Canada",
        "region": "North America",
        "description": "Mountains meet the ocean in this laid-back Pacific coast city.",
        "budget_per_day": 180,
        "interests": "scenery,hiking,food",
        "uniqueness_score": 6,
        "travel_difficulty": 2,
        "latitude": 49.2827,
        "longitude": -123.1207,
        "currency": "CAD",
        # Dry, sunny summer (Jun-Aug) peak; rainy winter cheapest.
        "seasonal_multipliers": "0.90,0.90,0.95,1.00,1.05,1.15,1.25,1.20,1.05,0.95,0.90,1.05",
        "activities": [
            {
                "name": "Stanley Park Seawall Bike Ride", "category": "outdoor", "price": 20, "duration_hours": 2.5,
                "location": "Stanley Park", "opening_time": "07:00", "closing_time": "21:00", "travel_minutes": 10,
                "latitude": 49.3017, "longitude": -123.1417, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Mexico City",
        "country": "Mexico",
        "region": "North America",
        "description": "Ancient pyramids, world-class museums, and one of the world's great food scenes.",
        "budget_per_day": 80,
        "interests": "food,history,art",
        "uniqueness_score": 7,
        "travel_difficulty": 3,
        "latitude": 19.4326,
        "longitude": -99.1332,
        "currency": "MXN",
        # Mild high-altitude climate year-round; holiday season (Dec) and spring peak slightly.
        "seasonal_multipliers": "1.05,1.00,1.05,1.05,1.00,0.90,0.85,0.85,0.90,0.95,1.00,1.15",
        "activities": [
            {
                "name": "Teotihuacan Pyramids Day Trip", "category": "history", "price": 45, "duration_hours": 6,
                "location": "Teotihuacan", "opening_time": "08:00", "closing_time": "16:00", "travel_minutes": 60,
                "latitude": 19.6925, "longitude": -98.8438, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Cabo San Lucas",
        "country": "Mexico",
        "region": "North America",
        "description": "Dramatic desert-meets-ocean landscapes and sport-fishing charters.",
        "budget_per_day": 190,
        "interests": "beaches,adventure,relaxation",
        "uniqueness_score": 6,
        "travel_difficulty": 3,
        "latitude": 22.8905,
        "longitude": -109.9167,
        "currency": "MXN",
        # Dry, mild winter (Dec-Apr) peak; hot, humid summer cheapest.
        "seasonal_multipliers": "1.25,1.25,1.20,1.10,0.90,0.80,0.80,0.80,0.75,0.90,1.05,1.30",
        "activities": [
            {
                "name": "El Arco Sunset Boat Tour", "category": "relaxation", "price": 55, "duration_hours": 2,
                "location": "Marina Cabo San Lucas", "opening_time": "16:00", "closing_time": "19:00", "travel_minutes": 10,
                "latitude": 22.8837, "longitude": -109.9096, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Rio de Janeiro",
        "country": "Brazil",
        "region": "South America",
        "description": "Iconic beaches, samba rhythms, and Christ the Redeemer overlooking it all.",
        "budget_per_day": 110,
        "interests": "beaches,culture,scenery",
        "uniqueness_score": 8,
        "travel_difficulty": 4,
        "latitude": -22.9068,
        "longitude": -43.1729,
        "currency": "BRL",
        # Southern Hemisphere summer (Dec-Feb) plus Carnival peak; winter (Jun-Aug) quiet.
        "seasonal_multipliers": "1.35,1.30,1.25,1.00,0.85,0.75,0.75,0.80,0.85,0.90,1.05,1.35",
        "activities": [
            {
                "name": "Christ the Redeemer & Sugarloaf Mountain", "category": "scenery", "price": 60, "duration_hours": 5,
                "location": "Corcovado", "opening_time": "08:00", "closing_time": "19:00", "travel_minutes": 30,
                "latitude": -22.9519, "longitude": -43.2105, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Cusco",
        "country": "Peru",
        "region": "South America",
        "description": "Inca capital and the gateway to Machu Picchu high in the Andes.",
        "budget_per_day": 70,
        "interests": "history,hiking,culture",
        "uniqueness_score": 9,
        "travel_difficulty": 6,
        "latitude": -13.5319,
        "longitude": -71.9675,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "PEN",
        # Andean dry season (May-Sep) peak for trekking; wet season (Dec-Mar) cheaper.
        "seasonal_multipliers": "0.85,0.80,0.85,1.00,1.15,1.25,1.30,1.25,1.10,1.00,0.90,0.85",
        "activities": [
            {
                "name": "Machu Picchu Guided Day Tour", "category": "history", "price": 120, "duration_hours": 10,
                "location": "Machu Picchu", "opening_time": "05:00", "closing_time": "17:00", "travel_minutes": 120,
                "latitude": -13.1631, "longitude": -72.5450, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Arenal Volcano",
        "country": "Costa Rica",
        "region": "North America",
        "description": "Rainforest hot springs beneath a still-active volcano.",
        "budget_per_day": 130,
        "interests": "adventure,relaxation,wildlife",
        "uniqueness_score": 8,
        "travel_difficulty": 5,
        "latitude": 10.4679,
        "longitude": -84.6435,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "CRC",
        # Dry season (Dec-Apr) peak; green/rainy season (May-Nov) cheaper.
        "seasonal_multipliers": "1.25,1.25,1.20,1.10,0.90,0.80,0.80,0.80,0.75,0.80,1.00,1.25",
        "activities": [
            {
                "name": "Arenal Hot Springs & Volcano View", "category": "relaxation", "price": 65, "duration_hours": 3,
                "location": "La Fortuna", "opening_time": "11:00", "closing_time": "22:00", "travel_minutes": 15,
                "latitude": 10.4633, "longitude": -84.7020, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Sydney",
        "country": "Australia",
        "region": "Oceania",
        "description": "Harbourside icons, ocean beaches, and laid-back Australian energy.",
        "budget_per_day": 200,
        "interests": "beaches,scenery,culture",
        "uniqueness_score": 7,
        "travel_difficulty": 5,
        "latitude": -33.8688,
        "longitude": 151.2093,
        "currency": "AUD",
        # Southern Hemisphere summer (Dec-Feb) peak; winter (Jun-Aug) quietest.
        "seasonal_multipliers": "1.30,1.25,1.10,0.95,0.85,0.80,0.80,0.85,0.90,1.00,1.10,1.35",
        "activities": [
            {
                "name": "Sydney Opera House & Harbour Bridge Walk", "category": "sightseeing", "price": 45, "duration_hours": 2.5,
                "location": "Circular Quay", "opening_time": "09:00", "closing_time": "20:00", "travel_minutes": 10,
                "latitude": -33.8568, "longitude": 151.2153, "is_outdoor": True,
            },
            {
                "name": "Bondi to Coogee Coastal Walk", "category": "hiking", "price": 0, "duration_hours": 2.5,
                "location": "Bondi Beach", "opening_time": "06:00", "closing_time": "19:00", "travel_minutes": 20,
                "latitude": -33.8908, "longitude": 151.2743, "is_outdoor": True,
            },
        ],
    },
    {
        "name": "Dubai",
        "country": "United Arab Emirates",
        "region": "Middle East",
        "description": "Futuristic skyscrapers, desert dunes, and lavish shopping malls.",
        "budget_per_day": 250,
        "interests": "shopping,adventure,scenery",
        "uniqueness_score": 8,
        "travel_difficulty": 2,
        "latitude": 25.2048,
        "longitude": 55.2708,
        # Not covered by Frankfurter (see backpacker_optimizations.md, currency arbitrage).
        "currency": "AED",
        # Mild winter (Nov-Mar) peak; brutal desert summer heat cheapest.
        "seasonal_multipliers": "1.25,1.20,1.10,0.95,0.80,0.70,0.65,0.65,0.80,1.00,1.15,1.30",
        "activities": [
            {
                "name": "Burj Khalifa Observation Deck", "category": "sightseeing", "price": 45, "duration_hours": 1.5,
                "location": "Downtown Dubai", "opening_time": "08:30", "closing_time": "23:00", "travel_minutes": 15,
                "latitude": 25.1972, "longitude": 55.2744, "is_outdoor": False,
            },
            {
                "name": "Desert Safari & Dune Bashing", "category": "adventure", "price": 75, "duration_hours": 6,
                "location": "Dubai Desert Conservation Reserve", "opening_time": "15:00", "closing_time": "21:00",
                "travel_minutes": 45, "latitude": 24.9857, "longitude": 55.7500, "is_outdoor": True,
            },
        ],
    },
]


# Extra tags layered on top of each hand-curated activity's own category, so
# interest matching (see itinerary.py) can score partial matches -- same
# purpose and spirit as osm_activities.py's _CATEGORY_SYNONYMS, just against
# this dataset's own freer category vocabulary rather than OSM's.
_SEED_CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "adventure": ["outdoors", "thrill"],
    "art": ["culture", "gallery"],
    "culture": ["history", "sightseeing"],
    "food": ["dining", "local"],
    "hiking": ["outdoors", "nature"],
    "history": ["culture", "sightseeing"],
    "nightlife": ["bar", "drinks", "entertainment"],
    "outdoor": ["outdoors", "nature"],
    "relaxation": ["wellness"],
    "scenery": ["nature", "photography", "sightseeing"],
    "sightseeing": ["culture", "photography"],
    "skiing": ["outdoor_recreation", "winter_sports", "adventure"],
    "surfing": ["outdoor_recreation", "water", "adventure"],
    "theme-parks": ["entertainment", "family"],
    "wildlife": ["nature", "outdoors"],
}


def _expand_seed_activity(activity: dict) -> dict:
    """Fills in `tags` and `neighborhood` for a hand-curated seed activity,
    best-effort, without requiring every one of the ~90 entries above to be
    hand-edited. `neighborhood` defaults to the existing `location` string,
    which is already a neighborhood/city label rather than a full street
    address for this dataset (see Activity.location's docstring)."""
    expanded = dict(activity)
    category = expanded.get("category")
    if category:
        synonyms = _SEED_CATEGORY_SYNONYMS.get(category, [])
        expanded.setdefault("tags", ",".join([category, *synonyms]))
    expanded.setdefault("neighborhood", expanded.get("location"))
    return expanded


def seed_sample_data(db: Session) -> None:
    """Insert the sample dataset if the destinations table is currently empty."""
    if db.query(Destination).first() is not None:
        return

    for raw_entry in SAMPLE_DESTINATIONS:
        entry = dict(raw_entry)
        activities_data = entry.pop("activities", [])
        airports_data = entry.pop("airports", [])
        destination = Destination(**entry)
        destination.activities = [Activity(**_expand_seed_activity(activity)) for activity in activities_data]
        destination.airports = [Airport(**airport) for airport in airports_data]
        db.add(destination)

    db.commit()
