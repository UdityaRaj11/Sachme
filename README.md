# Sachme — AI-Powered Information Firewall

An enterprise-grade, explainable AI information firewall backend that verifies online content in seconds. It accepts URLs from social media platforms, video networks, and news websites, understands and summarizes multimodal content, extracts factual claims, gathers evidence from tiered authoritative sources, evaluates credibility, and delivers explainable, evidence-grounded verification results.

---

## 🏛️ Architecture Overview

Sachme is architected as an asynchronous, modular microservice pipeline designed for high-throughput, low-latency epistemic verification.

```
User / Client
      │
      ▼
[1. URL / Content Classifier] ─── (Rejects malicious/unsupported URLs with 422/400)
      │
      ▼
[2. Content Extraction Pipeline]
      ├── Webpage (Trafilatura + Metadata)
      ├── YouTube Video / Shorts (Transcripts + oEmbed)
      ├── Social Media (X/Twitter, Instagram Reels & Posts)
      ├── Direct Image (Metadata + Dimensions + OCR Context)
      └── Direct Text Submission
      │
      ▼
[3. Multimodal Summarizer] ─── (Visual context, spoken transcripts, key points)
      │
      ▼
[4. Claim Extraction Engine] ─── (Separates verifiable facts from opinions/satire)
      │
      ▼
[5. Evidence Retrieval Engine] ─── (Generates targeted investigative questions)
      │
      ▼
[6. Source Credibility Engine] ─── (Configurable weighted 0-100 scoring: Tier 1 > 2 > 3)
      │
      ▼
[7. Claim Verification Engine] ─── (Cross-checks claim vs evidence: Stance, Consensus)
      │
      ▼
[8. Confidence Engine] ─── (Computes 0-100 score in VERDICT certainty)
      │
      ▼
[9. Explanation & UI Layer] ─── (Evidence → Reasoning → Verdict + UI breakdown)
      │
      ▼
Structured JSON Response
```

---

## 🛡️ Epistemic Safety & Reliability Principles

1. **Zero Hallucination Guarantee**: The system never invents missing content. Extracted facts are strictly isolated from inferred context.
2. **Strict Provenance**: Every verdict references explicit source URLs, publisher titles, and exact text excerpts.
3. **External Grounding Over Model Memory**: The system does NOT rely on the LLM's pre-trained parametric memory to judge truth. If external evidence is absent or contradictory, the verdict is strictly marked `UNVERIFIABLE`.
4. **Reliability ≠ Automatic Truth**: Government portals (Tier 1) receive high source credibility because they represent official legal records, but the system **never hardcodes "government = always true"**.
5. **Nuanced Stances**: Avoids naive binary TRUE/FALSE decisions when evidence is partial or context is omitted, explicitly utilizing `MISLEADING` and `UNVERIFIABLE`.

---

## 📊 Source Credibility Scoring Formula

Each source receives a credibility score (0–100) computed dynamically from configurable YAML weights (`config/credibility_weights.yaml`):

$$\text{Score} = \frac{\sum (W_i \cdot S_i)}{\sum W_i}$$

### Configurable Factors:
* **Tier Weight ($W = 0.35$)**:
  * **Tier 1 (Base: 90)**: Government ministries (`.gov`, `.gov.in`, `.nic.in`), regulatory bodies (RBI, WHO, CDC, FDA, NASA), official gazettes, peer-reviewed scientific journals (*Nature*, *Science*, *The Lancet*).
  * **Tier 2 (Base: 75)**: High-credibility secondary sources (Reuters, AP News, BBC, NYT), accredited fact-checkers (Snopes, Alt News, FactCheck.org, PolitiFact), academic institutions (`.edu`, `.ac.uk`).
  * **Tier 3 (Base: 45)**: General web, blogs, forums, social media, user-generated content.
* **Domain Reputation ($W = 0.25$)**: Indexed against known domain authority databases.
* **Semantic & Entity Relevance ($W = 0.15$)**: Token and entity overlap with the target claim.
* **Primary Source Bonus ($W = 0.10$)**: Direct primary documentation vs. secondary commentary.
* **Recency & Freshness ($W = 0.08$)**: Temporal alignment with the claim events.
* **Multi-Source Corroboration ($W = 0.07$)**: Boosted when 3+ independent sources corroborate.

> **Dynamic Reconfiguration**: Weights can be modified at runtime via `POST /api/v1/config/credibility-weights` without server restarts.

---

## 🎯 Verdict Categories & Confidence Scoring

### Verdict Categories:
* `SUPPORTED`: Available credible evidence substantially confirms the claim.
* `MISLEADING`: Claim contains elements of truth but omits context, cherry-picks facts, or creates an incorrect impression.
* `CONTRADICTED`: Reliable evidence directly refutes the claim (e.g. scams, viral debunks).
* `UNVERIFIABLE`: Insufficient reliable evidence to determine truth.
* `OPINION`: Subjective viewpoints, predictions, satire, or value judgements.

### Confidence Score (0–100):
Confidence reflects **certainty in the verdict**, not the probability that the claim itself is true:
* High-confidence `CONTRADICTED` (e.g. 94%) = High certainty that the claim is false.
* High-confidence `UNVERIFIABLE` (e.g. 85%) = High certainty that credible documentation does not exist.
* Conflicting sources automatically depress confidence (capped at 70%).
* Tier 3 sources alone cannot yield confidence exceeding 65%.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Virtual environment (recommended)

### Installation
```bash
# Clone repository
git clone <repo-url>
cd Igniters

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Copy `.env.example` to `.env` and set optional API keys:
```bash
cp .env.example .env
```

```env
# AI Provider: 'gemini', 'openai', or 'heuristic' (zero-config local fallback)
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Search Provider: 'duckduckgo', 'tavily', or 'serpapi'
SEARCH_PROVIDER=duckduckgo
TAVILY_API_KEY=your-tavily-api-key

# Server Settings
HOST=0.0.0.0
PORT=8000
RATE_LIMIT_PER_MINUTE=60
CACHE_TTL_SECONDS=3600
```

*Note: If no API keys are configured, the system seamlessly uses its high-fidelity deterministic heuristic engine and live DuckDuckGo / Curated search out of the box.*

### Running the API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be live at `http://localhost:8000/docs`.

---

## 📡 API Reference

### 1. Synchronous Verification
`POST /api/v1/verify/sync`

Executes the entire verification pipeline synchronously and returns the complete result.

#### Request:
```json
{
  "url": null,
  "direct_text": "Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz",
  "language_preference": "en"
}
```

#### Response (Strict Section 10 & 11 Schema):
```json
{
  "status": "success",
  "content": {
    "url": "text://direct-input",
    "platform": "text_direct",
    "content_type": "text",
    "language": "en",
    "summary": {
      "visual": null,
      "text": "Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz",
      "key_points": [
        "Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz"
      ]
    }
  },
  "claims": [
    {
      "claim_id": "c_1",
      "claim": "Government is giving ₹25,000 to every student",
      "verdict": "CONTRADICTED",
      "confidence": 94,
      "evidence": [
        {
          "finding": "PIB Fact Check: A viral message claiming the Central Government is providing ₹25,000 financial assistance to every student is completely fraudulent. No such scheme has been launched by any Ministry. Do not click on unverified registration links.",
          "type": "contradicting",
          "source": "Press Information Bureau (PIB)",
          "url": "https://pib.gov.in/FactCheck/FakeStudentScheme2026.html",
          "credibility_score": 96
        },
        {
          "finding": "Official advisory: The Ministry of Education warns students against fraudulent portals claiming direct cash transfers of ₹25,000. All official scholarships are hosted exclusively on scholarships.gov.in.",
          "type": "contradicting",
          "source": "Ministry of Education (gov.in)",
          "url": "https://education.gov.in/en/updates/fake-scholarship-alert",
          "credibility_score": 95
        },
        {
          "finding": "Alt News investigation found the registration URL circulates on WhatsApp and leads to phishing websites stealing banking credentials. Ministry of Education confirmed no such cash distribution scheme exists.",
          "type": "contradicting",
          "source": "Alt News Fact Check",
          "url": "https://altnews.in/fact-check-central-government-scholarship-fraud/",
          "credibility_score": 89
        }
      ],
      "explanation": "EVIDENCE: Cross-checked against 3 independent sources including Press Information Bureau (PIB) (Credibility: 96/100), Ministry of Education (gov.in) (Credibility: 95/100). Key finding: \"PIB Fact Check: A viral message claiming the Central Government is providing ₹25,000 financial assistance to every student is completely fraudulent.\". REASONING: Available evidence from 3 sources refutes the assertion. Primary sources indicate this claim does not align with verifiable facts. VERDICT: CONTRADICTED."
    }
  ],
  "overall_verdict": "CONTRADICTED",
  "overall_confidence": 94,
  "user_interface": {
    "badge_label": "❌ False / Disproven",
    "claim_detected": "Government is giving ₹25,000 to every student",
    "evidence_points": [
      "❌ Press Information Bureau (PIB): PIB Fact Check: A viral message claiming the Central Government is providing ₹25,000 financial assistance...",
      "❌ Ministry of Education (gov.in): Official advisory: The Ministry of Education warns students against fraudulent portals claiming direct cash...",
      "❌ Alt News Fact Check: Alt News investigation found the registration URL circulates on WhatsApp and leads to phishing websites..."
    ],
    "verdict_title": "Disproven / Misinformation",
    "confidence_display": "94%",
    "why_explanation": "Directly contradicted by credible reporting from Press Information Bureau (PIB).",
    "evidence_sources": [
      {
        "source": "Press Information Bureau (PIB)",
        "url": "https://pib.gov.in/FactCheck/FakeStudentScheme2026.html",
        "credibility": "96/100"
      },
      {
        "source": "Ministry of Education (gov.in)",
        "url": "https://education.gov.in/en/updates/fake-scholarship-alert",
        "credibility": "95/100"
      },
      {
        "source": "Alt News Fact Check",
        "url": "https://altnews.in/fact-check-central-government-scholarship-fraud/",
        "credibility": "89/100"
      }
    ]
  }
}
```

---

### 2. Asynchronous Job Creation & Polling
`POST /api/v1/verify` (202 Accepted)

Submits video, audio, or social media links for non-blocking background analysis:
```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

```json
{
  "status": "queued",
  "job_id": "782fc9bb-361f-4efc-8b83-a0e28d0ee5df",
  "poll_url": "/api/v1/jobs/782fc9bb-361f-4efc-8b83-a0e28d0ee5df",
  "message": "Verification job initiated. Poll poll_url to retrieve live progress and final result."
}
```

Poll Job Progress:
`GET /api/v1/jobs/{job_id}`
```json
{
  "job_id": "782fc9bb-361f-4efc-8b83-a0e28d0ee5df",
  "status": "verifying",
  "progress_percentage": 85,
  "current_step": "Cross-checking claim 1 against gathered evidence...",
  "result": null,
  "error": null,
  "created_at": "2026-10-04T17:35:00Z",
  "completed_at": null
}
```

---

### 3. Dynamic Credibility Configuration
* `GET /api/v1/config/credibility-weights` — Inspect active formula weights.
* `POST /api/v1/config/credibility-weights` — Dynamically adjust factor weights at runtime.

---

## 🧪 Running the Test Suite

Run the full automated test suite with pytest:
```bash
pytest -v
```

### Test Coverage includes:
* **Platform & Content Classification**: Web articles, YouTube videos/Shorts, X/Twitter, Instagram reels, images, text, and SSRF/malicious payload prevention.
* **Source Credibility Scoring**: Government TLD evaluation, Tier 1/2/3 separation, recency, corroboration bonus, dynamic weight updates.
* **Confidence Engine**: Agreement calculations, evidence volume thresholds, Tier-3 confidence capping, conflict penalties.
* **Claim Verification & Stance**: Grounded debunks, supported official announcements, opinion filtering, Evidence → Reasoning → Verdict compliance.
* **API Endpoints**: Synchronous verification, async job queuing & polling, rate limiting, and 422 error enforcement.
