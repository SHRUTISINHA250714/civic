from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.routers.deps import get_current_active_user, get_current_admin
from backend.app.services.predictive import predictive_service

router = APIRouter(prefix="/predictive", tags=["Predictive Analytics & Forecasting"])


class EstimateRequest(BaseModel):
    category: str
    ward: Optional[str] = "Central"
    priority: Optional[str] = "Medium"
    department: Optional[str] = "BBMP"


@router.get("/overview", response_model=Dict[str, Any])
def get_predictive_overview(
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns high-level early warning KPI metrics, top hotspot zones, 
    and 14-day grievance forecasts.
    """
    return predictive_service.get_predictive_overview()


@router.post("/estimate", response_model=Dict[str, Any])
def estimate_complaint_risk(
    req: EstimateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Evaluates ML SLA breach probability & expected resolution time 
    given category, ward, priority, and department.
    """
    return predictive_service.predict_complaint_risk(
        category=req.category,
        ward=req.ward or "Central",
        priority=req.priority or "Medium",
        dept=req.department or "BBMP"
    )


@router.get("/hotspots", response_model=List[Dict[str, Any]])
def get_hotspot_predictions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns zone and ward-level risk rankings with monsoon surge multipliers.
    """
    return predictive_service.get_hotspot_forecasts()


@router.get("/forecast", response_model=Dict[str, Any])
def get_time_series_forecast(
    days: int = 14,
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns time-series daily grievance intake projections for the next N days.
    """
    return predictive_service.get_time_series_forecast(days_ahead=days)


@router.post("/train", response_model=Dict[str, Any])
def retrain_predictive_models(
    max_samples: int = 100000,
    current_user: User = Depends(get_current_admin)
):
    """
    Admin-only: Retrains the Random Forest SLA breach classifier and 
    resolution regressor on the historical Karnataka grievance dataset.
    """
    stats = predictive_service.train_on_historical_dataset(max_samples=max_samples)
    return {
        "message": "Predictive ML models successfully retrained and cached.",
        "training_stats": stats
    }
