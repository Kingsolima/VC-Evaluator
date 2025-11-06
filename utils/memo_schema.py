# memo_schema.py - Enhanced with StartupInfo from core.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class StartupInfo(BaseModel):
    """Main data model for startup pitch submissions"""
    # Core fields
    name: str
    website: str
    round: str
    investors: str
    traction: str
    team: str
    product: str
    email_to: str
    
    # Early stage specific fields (from Typeform)
    industry: Optional[str] = ""
    round_size: Optional[str] = ""
    revenue: Optional[str] = ""
    customers: Optional[str] = ""
    market_size: Optional[str] = ""
    problem: Optional[str] = ""
    solution: Optional[str] = ""
    business_model: Optional[str] = ""
    market: Optional[str] = ""
    competition: Optional[str] = ""
    moat: Optional[str] = ""
    risks: Optional[str] = ""
    vision: Optional[str] = ""
    product_stage: Optional[str] = ""
    pitch_deck: Optional[str] = ""
    
    # Enhanced founder fields
    founder_1_name: Optional[str] = ""
    founder_1_background: Optional[str] = ""
    founder_1_linkedin: Optional[str] = ""
    founder_2_name: Optional[str] = ""
    founder_2_background: Optional[str] = ""
    founder_2_linkedin: Optional[str] = ""
    founder_3_name: Optional[str] = ""
    founder_3_background: Optional[str] = ""
    founder_3_linkedin: Optional[str] = ""

class TeamMember(BaseModel):
    name: str
    role: str
    linkedin: Optional[str] = None
    highlights: List[str] = []

class Competitor(BaseModel):
    name: str
    note: str

class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for investment decision"""
    team: int = 0
    market: int = 0
    product: int = 0
    vision: int = 0
    traction: int = 0
    business_model: int = 0
    moat: int = 0
    risk_adj: int = 0
    bonus: int = 0

class InvestmentScorecard(BaseModel):
    """Investment scorecard with verdict"""
    scores: ScoreBreakdown
    total: int
    verdict: str  # TAKE_CALL, LEARN_MORE, PASS

class MemoPayload(BaseModel):
    """Complete memo payload for structured data extraction"""
    company: str
    website: str
    round: str
    industry: str
    synopsis: str
    problem: str
    solution: str
    business_model: str
    market_size: Dict[str, str]  # {"TAM": "...", "SAM": "...", "SOM": "..."}
    gtm: str
    traction: Dict[str, Any]     # {"MRR": "...", "Growth": "...", "Logos": ["..."], "Metrics": ["..."]}
    competitors: List[Competitor]
    team: List[TeamMember]
    cap_table: Optional[str] = None
    risks: List[str] = []
    milestones: List[str] = []
    use_of_funds: List[str] = []
    ask: Dict[str, str]         # {"raise": "...", "valuation": "...", "terms": "..."}
    exit_strategy: Optional[str] = None
    press: List[str] = []
    scorecard: InvestmentScorecard