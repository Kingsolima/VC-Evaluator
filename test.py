import requests
import json

payload = {
    "form_response": {
        "answers": [
            { "field": { "title": "Company Name ?" }, "text": "AcmeAI" },
            { "field": { "title": "Company website?" }, "text": "https://acme.ai" },
            { "field": { "title": "Which series are you looking to raise?" }, "text": "Seed" },
            { "field": { "title": "Do you have a lead investor for this round? If so, please include their name" }, "text": "a16z" },
            { "field": { "title": "Traction" }, "text": "20k MRR, 50 Percent MoM" },
            { "field": { "title": "Team" }, "text": "2 ex-Google engineers" },
            { "field": { "title": "Solution" }, "text": "AI assistant for lawyers" },
            { "field": { "title": "Whats your first name?" }, "text": "Jane" },
            { "field": { "title": "Whats your last name?" }, "text": "Doe" },
            { "field": { "title": "Whats your email address, Omar?" }, "email": "solimam@gmail.com" },
            { "field": { "title": "Where is the company incorporated?" }, "text": "Delaware" },
            { "field": { "title": "Position in the company?" }, "text": "CEO" },
            { "field": { "title": "Problem" }, "text": "Lawyers waste time on admin." },
            { "field": { "title": "Solution" }, "text": "AI handles client intake and doc generation" },
            { "field": { "title": "Market" }, "text": "30B legaltech market" },
            { "field": { "title": "What university did you attend?" }, "text": "MIT" },
            { "field": { "title": "Competition" }, "text": "Ironclad, Spellbook" },
            { "field": { "title": "Milestones to Next Round" }, "text": "Hit 100k MRR in 9 months" },
            { "field": { "title": "Vision" }, "text": "Be the Salesforce of legal ops" },
            { "field": { "title": "Round Size" }, "text": "$4M ($3.5M committed)" },
            { "field": { "title": "Industry" }, "text": "AI SaaS / LegalTech" },
            { "field": { "title": "Business Model" }, "text": "Recurring revenue, priced per seat" },
            { "field": { "title": "Product Stage" }, "text": "Live with 10 paying customers" },
            { "field": { "title": "Moat" }, "text": "Proprietary dataset from 50k legal documents" },
            { "field": { "title": "Risks" }, "text": "Selling into slow-moving legal firms" },
            { "field": { "title": "Cap Table" }, "text": "YC, a16z, Naval Ravikant" },

        ]
    }
}

response = requests.post(
    "http://localhost:8000/webhook/typeform-webhook",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

print("✅ Status:", response.status_code)
print("📦 Response:", response.json())
