from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class PropertyRecord(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    property_id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Property address")
    assessed_value: int = Field(..., description="Current assessed value")
    market_value: int = Field(..., description="Estimated market value")
    owner_name: str = Field(..., description="Property owner name")
    property_type: str = Field(..., description="Property type (Residential, Commercial, etc.)")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")


class AppealRecord(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    appeal_id: str = Field(..., description="Unique appeal identifier")
    property_id: str = Field(..., description="Associated property ID")
    appeal_date: str = Field(..., description="Date appeal was filed")
    status: str = Field(..., description="Current appeal status")
    requested_value: int = Field(..., description="Value requested in appeal")
    reason: str = Field(..., description="Reason for appeal")
    hearing_date: Optional[str] = Field(default=None, description="Scheduled hearing date")
    resolution: Optional[str] = Field(default=None, description="Appeal resolution")
    final_value: Optional[int] = Field(default=None, description="Final assessed value")


class CollectionResult(BaseModel):
    property_records: list[PropertyRecord] = Field(default_factory=list)
    appeal_records: list[AppealRecord] = Field(default_factory=list)
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_properties: int = Field(default=0)
    total_appeals: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    errors: list[str] = Field(default_factory=list)