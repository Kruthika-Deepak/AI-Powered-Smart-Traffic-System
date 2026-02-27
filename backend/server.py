from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Bangalore Traffic Sentinel API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Supported traffic locations
TRAFFIC_LOCATIONS = {
    "silk_board": {"name": "Silk Board", "latitude": 12.9177, "longitude": 77.6233},
    "kr_puram": {"name": "KR Puram", "latitude": 13.0075, "longitude": 77.6959},
    "whitefield": {"name": "Whitefield", "latitude": 12.9698, "longitude": 77.7500},
    "hebbal": {"name": "Hebbal", "latitude": 13.0358, "longitude": 77.5970},
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Traffic prediction model (simulates realistic patterns)
def predict_traffic_value(place: str, day: str, hour: int) -> float:
    """
    Simulates ML model prediction based on realistic Bangalore traffic patterns.
    Returns PCU (Passenger Car Units) per hour.
    """
    base_traffic = {
        "silk_board": 2500,  # Highest congestion area
        "kr_puram": 2200,
        "whitefield": 1800,
        "hebbal": 2000,
    }
    
    base = base_traffic.get(place, 1500)
    
    # Weekend factor (lower traffic)
    is_weekend = day in ["Saturday", "Sunday"]
    weekend_factor = 0.6 if is_weekend else 1.0
    
    # Hour-based multiplier (rush hours)
    hour_multiplier = 1.0
    if 8 <= hour <= 10:  # Morning rush
        hour_multiplier = 1.8
    elif 17 <= hour <= 20:  # Evening rush
        hour_multiplier = 2.0
    elif 12 <= hour <= 14:  # Lunch time
        hour_multiplier = 1.3
    elif 0 <= hour <= 5:  # Late night/early morning
        hour_multiplier = 0.3
    elif 22 <= hour <= 23:  # Late night
        hour_multiplier = 0.5
    
    # Day variations
    day_factor = 1.0
    if day == "Friday":
        day_factor = 1.15
    elif day == "Monday":
        day_factor = 1.1
    
    # Calculate traffic with some randomness
    traffic = base * weekend_factor * hour_multiplier * day_factor
    traffic = traffic * (0.9 + random.random() * 0.2)  # ±10% variation
    
    return round(traffic, 2)

def get_traffic_level(traffic_value: float) -> dict:
    """Determine traffic level and color based on PCU value"""
    if traffic_value < 1500:
        return {"level": "Normal", "color": "#10B981", "severity": 1}
    elif traffic_value < 2500:
        return {"level": "Moderate", "color": "#F59E0B", "severity": 2}
    else:
        return {"level": "High", "color": "#EF4444", "severity": 3}


# Pydantic Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class TrafficPredictionRequest(BaseModel):
    place: str
    day: str
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=0, le=23)

class HourlyPrediction(BaseModel):
    hour: int
    traffic_value: float
    traffic_level: str
    color: str
    severity: int

class TrafficPredictionResponse(BaseModel):
    place: str
    place_name: str
    latitude: float
    longitude: float
    day: str
    predictions: List[HourlyPrediction]
    peak_hour: int
    peak_traffic: float
    average_traffic: float
    insight: str

class LocationInfo(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Bangalore Traffic Sentinel API", "version": "1.0.0"}

@api_router.get("/locations", response_model=List[LocationInfo])
async def get_locations():
    """Get all supported traffic monitoring locations"""
    return [
        LocationInfo(id=loc_id, **loc_data)
        for loc_id, loc_data in TRAFFIC_LOCATIONS.items()
    ]

@api_router.get("/days")
async def get_days():
    """Get days of week"""
    return {"days": DAYS_OF_WEEK}

@api_router.post("/predict-traffic", response_model=TrafficPredictionResponse)
async def predict_traffic_range(request: TrafficPredictionRequest):
    """
    Predict traffic for a location over a time range.
    This simulates the ML model prediction.
    """
    place = request.place.lower().replace(" ", "_")
    
    if place not in TRAFFIC_LOCATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid location. Supported locations: {list(TRAFFIC_LOCATIONS.keys())}"
        )
    
    if request.day not in DAYS_OF_WEEK:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid day. Supported days: {DAYS_OF_WEEK}"
        )
    
    if request.end_hour < request.start_hour:
        raise HTTPException(
            status_code=400,
            detail="End hour must be greater than or equal to start hour"
        )
    
    location = TRAFFIC_LOCATIONS[place]
    predictions = []
    
    for hour in range(request.start_hour, request.end_hour + 1):
        traffic_value = predict_traffic_value(place, request.day, hour)
        level_info = get_traffic_level(traffic_value)
        predictions.append(HourlyPrediction(
            hour=hour,
            traffic_value=traffic_value,
            traffic_level=level_info["level"],
            color=level_info["color"],
            severity=level_info["severity"]
        ))
    
    # Calculate insights
    peak_prediction = max(predictions, key=lambda x: x.traffic_value)
    average_traffic = sum(p.traffic_value for p in predictions) / len(predictions)
    
    # Generate insight
    if peak_prediction.severity == 3:
        insight = f"Peak congestion expected at {peak_prediction.hour}:00. Consider alternative routes or delay travel by 1-2 hours."
    elif peak_prediction.severity == 2:
        insight = f"Moderate traffic expected. {peak_prediction.hour}:00 shows highest activity. Plan buffer time."
    else:
        insight = f"Traffic conditions are favorable. Smooth commute expected throughout the selected time range."
    
    # Store prediction in DB for analytics
    prediction_doc = {
        "id": str(uuid.uuid4()),
        "place": place,
        "day": request.day,
        "start_hour": request.start_hour,
        "end_hour": request.end_hour,
        "peak_hour": peak_prediction.hour,
        "peak_traffic": peak_prediction.traffic_value,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.traffic_predictions.insert_one(prediction_doc)
    
    return TrafficPredictionResponse(
        place=place,
        place_name=location["name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        day=request.day,
        predictions=predictions,
        peak_hour=peak_prediction.hour,
        peak_traffic=peak_prediction.traffic_value,
        average_traffic=round(average_traffic, 2),
        insight=insight
    )

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
