# utils/memo_schema.py
from typing import List, Optional
from pydantic import BaseModel

class TeamMember(BaseModel):
    name: str
    role: str
    linkedin: Optional[str] = None
    highlights: List[str] = []

class Competitor(BaseModel):
    name: str
    note: str

class MemoPayload(BaseModel):
    company: str
    website: str
    round: str
    industry: str
    synopsis: str
    problem: str
    solution: str
    business_model: str
    market_size: dict  # {"TAM": "...", "SAM": "...", "SOM": "..."}
    gtm: str
    traction: dict     # {"MRR": "...", "Growth": "...", "Logos": ["..."], "Metrics": ["..."]}
    competitors: List[Competitor]
    team: List[TeamMember]
    cap_table: Optional[str] = None
    risks: List[str] = []
    milestones: List[str] = []
    use_of_funds: List[str] = []
    ask: dict         # {"raise": "...", "valuation": "...", "terms": "..."}
    exit_strategy: Optional[str] = None
    press: List[str] = []
    scorecard: dict   # your totals/verdict + subscores
