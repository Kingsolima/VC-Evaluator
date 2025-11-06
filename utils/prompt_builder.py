# utils/prompt_builder.py - Prompt construction logic extracted from core.py
from typing import Dict, Any, Optional
from memo_schema import StartupInfo

def build_comprehensive_team_section(info: StartupInfo) -> str:
    """Build detailed team section from founder information"""
    team_backgrounds = []
    
    # Founder 1
    if getattr(info, 'founder_1_name', ''):
        founder_1_section = f"""
**{info.founder_1_name}**
Background: {getattr(info, 'founder_1_background', 'No background provided')}
LinkedIn: {getattr(info, 'founder_1_linkedin', 'Not provided')}
"""
        team_backgrounds.append(founder_1_section.strip())
    
    # Founder 2
    if getattr(info, 'founder_2_name', ''):
        founder_2_section = f"""
**{info.founder_2_name}**
Background: {getattr(info, 'founder_2_background', 'No background provided')}
LinkedIn: {getattr(info, 'founder_2_linkedin', 'Not provided')}
"""
        team_backgrounds.append(founder_2_section.strip())
    
    # Founder 3
    if getattr(info, 'founder_3_name', ''):
        founder_3_section = f"""
**{info.founder_3_name}**
Background: {getattr(info, 'founder_3_background', 'No background provided')}
LinkedIn: {getattr(info, 'founder_3_linkedin', 'Not provided')}
"""
        team_backgrounds.append(founder_3_section.strip())

    # Combine with original team info
    detailed_team_section = f"""
{info.team}

**Founder Details:**
{chr(10).join(team_backgrounds) if team_backgrounds else 'No detailed founder backgrounds provided'}
"""
    return detailed_team_section.strip()

def build_investment_memo_prompt(info: StartupInfo, extra: Optional[Dict[str, Any]] = None) -> str:
    """Build the complete prompt for investment memo generation - moved from core.py"""
    extra = extra or {}

    # Extract all fields from extra context and info
    problem = extra.get("problem", "") or getattr(info, 'problem', '')
    solution = extra.get("solution", "") or getattr(info, 'solution', '') 
    market = extra.get("market", "") or getattr(info, 'market', '')
    business_model = extra.get("business_model", "") or getattr(info, 'business_model', '')
    traction_detail = extra.get("traction_detail", "") or info.traction
    competition = extra.get("competition", "") or getattr(info, 'competition', '')
    moat = extra.get("moat", "") or getattr(info, 'moat', '')
    risks = extra.get("risks", "") or getattr(info, 'risks', '')
    vision = extra.get("vision", "") or getattr(info, 'vision', '')
    product_stage = extra.get("product_stage", "") or getattr(info, 'product_stage', '')
    round_size = extra.get("round_size", "") or getattr(info, 'round_size', '')
    industry = extra.get("industry", "") or getattr(info, 'industry', '')
    
    # Build comprehensive team section
    team_section = build_comprehensive_team_section(info)
    
    return f"""
You are a venture capital associate writing two outputs:

First, a **mini deal memo email** using the real company info below. Then, a comprehensive investor memo for PDF.

---

### MINI DEAL MEMO EMAIL

Hi GP,

Here is a mini memo for {info.name}, {info.product}. They are raising a {info.round} round, with interest from {info.investors}.

🏷️ **Startup Overview**
- **Name**: {info.name}
- **Website**: {info.website}
- **Industry**: {industry}
- **Round Stage**: {info.round}
- **Round Size**: {round_size}
- **Investors**: {info.investors}

📈 **Market**
{market}
{competition}

🔍 **Problem**
{problem}

🛠 **Solution**
{solution}

📊 **Traction**
{traction_detail}

💵 **Business Model**
{business_model}

🧱 **Moat / Defensibility**
{moat}

👥 **Team**
{team_section}

***Team Evaluation Instructions:***
When scoring the team section (0-25 points), carefully analyze the founder backgrounds provided above. Consider:

**Founders/CEO/CTO (0-15 points):**
- Previous startup experience and exits
- Industry domain expertise and years of experience  
- Technical skills relevant to the product
- Leadership roles and team management experience
- Educational background from relevant institutions
- Track record of shipping products or growing businesses

**Executive Team (0-10 points):**
- Complementary skills across product, engineering, sales, operations
- Prior experience at scale-stage companies
- Referenceable wins and achievements
- Hiring velocity and team-building capability

🚩 ***Red Flags / Risks***
{risks}

🧪 ***Product Stage***
{product_stage}

📊 ***Scorecard (computed)***
Compute scores using this rubric (max points):
- Team 0-25
    - Founders/CEO/CTO/VP of Engineering (0-15)
        - 12-15: Top-decile track record in relevant scenarios; elite recruiting magnet; shipped/operated at scale; excellent commercial instincts.
        - 9-11: Strong/top-quartile performance or senior leadership roles in related domains.
        - 4-8: Success in less-relevant roles; partial proof.
        - 0-3: Limited evidence for success in this context.
    - Executive Team (non founders) (0-10)
        - 8-10: Complementary skills (product, eng, sales, ops, finance), prior scale experience, referenceable wins, velocity.
        - 4-7: Good but with gaps to fill.
        - 0-3: Thin bench, single-threaded, or heavy contractor reliance. Or any serious leadership risk

- Market 0-20
    - 16-20 for a company that has secured paying customers, or rapid customer adoption. The market is large (in the billions) and growing.
    - 9-15 Company is in testing and in beta/non paying customers/or paid pilots. The market is large (in the billions) and growing.
    - 0-8 company has little to no customer feedback. Or the market is small (in the millions) and not growing fast enough.

- Traction 0-20
    - 14-20 for a company that has made significant progress given the amount of capital raised to date in traction, such as a large user base, high engagement, or high revenue.
    - 8-13 for a company that has moderate progress given the amount of capital raised to date in traction,, such as a growing user base, moderate engagement, or moderate revenue.
    - 0-7 for a company that has weak little progress given the amount of capital raised to date in traction, such as a small user base, low engagement, or low revenue.

- Business Model 0-10
    - 8-10 for a company that has unit economics and high scalability.
    - 4-7 for a company that has unit economics but questionable scalability (or vice versa).
    - 0-3 for a company that has questionable unit economics and scalability.

- Moat 0-25
    - 20-25 for a company that has a strong moat, such as a proprietary technology, technical complexity, IP, regulations, strong brand, or network effects.
    - 15-20 for a company that has average, moderate defensibility, competitors can enter market but gaining traction is relatively expensive or time intensive.
    - 10-15 for a company that has a weak moat, such as a commodity product, low technical complexity, no IP, no regulations, no strong brand, or no network effects. And competitors can easily enter the market without much effort, time, or cost.
    - 0-10 for a company that has no moat, such as a commodity product, low technical complexity, no IP, no regulations, no strong brand, or no network effects.

- Risk Adjustment 0 to -15 (if there isn't much risk don't adjust much, like 10 is for extreme cases)
    - Some reasons to adjust down:
        - The company is in a highly regulated industry.
        - The startup's main product can be just a feature in large companies.
        - The startup has a low moat and low traction.
        - The founders have limited experience in the industry.
        - The founders are old (50+).

- Bonus 0 to +10
    - +5 to +10 for a strong moat but very early stage and low traction.
    - 0 to +5 is up to the evaluator to decide.

Rules:
- Total = sum(all above) bounded to 0…100.
- Verdict mapping:
  - total ≥ 80 → "TAKE_CALL"
  - 70-79 → "LEARN_MORE"
  - 50-69 → "PASS"

After the email text, output ONE and only ONE ```json code block with scoring.

Allowed verdicts: TAKE_CALL, LEARN_MORE, PASS.

```json
{{"scores": {{"team": 0, "market": 0, "product": 0, "vision": 0, "traction": 0, "business_model": 0, "moat": 0, "risk_adj": 0, "bonus": 0}}, "total": 0, "verdict": "LEARN_MORE"}}
```

Best,  
VC Evaluator GPT

---

### COMPREHENSIVE INVESTMENT MEMO

Write a detailed institutional VC memo with these sections:

**EXECUTIVE SUMMARY**
- Investment recommendation and key metrics upfront
- 3-4 bullet points on investment highlights
- Risk summary

**INVESTMENT THESIS** 
- Why we're excited (2-3 paragraphs)
- What we like (3 specific points with evidence)  
- Key risks (3 specific concerns)

**COMPANY ANALYSIS**
- Problem (market pain, current solutions' failures)
- Solution (detailed product description, differentiation)
- Business model with unit economics table
- Market analysis with TAM/SAM/SOM breakdown
- Go-to-market strategy

**TRACTION & PERFORMANCE**
- Financial metrics table (ARR, MRR, customers, growth rates)
- KPIs (NRR, churn, CAC, LTV, payback period)
- Recent milestones with dates

**COMPETITIVE LANDSCAPE**  
- Direct competitors comparison table
- Competitive positioning and moats
- Switching costs and defensibility

**TEAM ASSESSMENT**
Use the detailed founder backgrounds to create comprehensive profiles:
- Founder backgrounds with specific experience and achievements
- Relevance of their experience to current venture
- Educational credentials and network
- Previous company exits or significant milestones
- Technical expertise alignment with product needs
- Advisory board and existing investors
- Team gaps and hiring plans

**FINANCIAL ANALYSIS**
- Funding history table
- Use of funds breakdown  
- 3-year financial projections
- Path to profitability

Use professional formatting, data tables, and quantitative analysis throughout.
"""

def enhance_team_scoring_context(info: StartupInfo) -> str:
    """Create additional context for GPT team scoring based on founder backgrounds"""
    scoring_context = []
    
    founders = [
        (getattr(info, 'founder_1_name', ''), getattr(info, 'founder_1_background', '')),
        (getattr(info, 'founder_2_name', ''), getattr(info, 'founder_2_background', '')),
        (getattr(info, 'founder_3_name', ''), getattr(info, 'founder_3_background', ''))
    ]
    
    for name, background in founders:
        if name and background:
            # Look for key experience indicators
            experience_signals = {
                'startup_experience': any(term in background.lower() for term in ['startup', 'founded', 'co-founder', 'exit', 'acquired']),
                'technical_experience': any(term in background.lower() for term in ['engineer', 'cto', 'developer', 'technical', 'software']),
                'leadership_experience': any(term in background.lower() for term in ['ceo', 'vp', 'director', 'head of', 'led team']),
                'industry_relevance': True  # This would need domain-specific logic
            }
            
            context = f"{name}: "
            context += ", ".join([k.replace('_', ' ') for k, v in experience_signals.items() if v])
            scoring_context.append(context)
    
    return "; ".join(scoring_context) if scoring_context else "Limited founder background information provided"