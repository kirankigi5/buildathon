
from typing import Optional, Dict
from pydantic import BaseModel

class StartupInput(BaseModel):
	name: str
	description: str
	industry: str = "Unknown"
	stage: str = "Seed"
	founder_name: Optional[str] = "Not provided"
	linkedin_url: Optional[str] = ""
	website: Optional[str] = ""
	total_raised_m: Optional[float] = 0.0
	location: Optional[str] = ""
	employees: Optional[int] = 0
	traction: Optional[str] = "Not disclosed"
	competitors: Optional[str] = ""

class StartupResult(BaseModel):
	name: str
	founder_name: str
	linkedin_url: str
	website: str
	tier: int  # 1, 2, or 3
	tier_label: str  # e.g. "🟢 Tier 1 - Immediate Accept"
	score: int  # 0-100
	invest: str  # "Yes", "No", or "Maybe"
	confidence: str  # "High", "Medium", or "Low"
	top_pro: str
	top_risk: str
	processing_time: float

class LogEvent(BaseModel):
	type: str  # "log", "result", "complete", "mapping", "startups"
	startup: Optional[str] = None
	message: Optional[str] = None
	agent: Optional[str] = None  # "nemotron", "claude", "gpt4", "system"
	data: Optional[Dict] = None
