# SkillStat AI — Intelligent Competency & Personalized Learning Platform
### Smart India Hackathon 2026 | Problem Statement PS26101

SkillStat AI is an AI-powered competency assessment, skill gap detection, and personalized learning platform engineered for civil servants, statistical officers, and public sector data analysts. Built in alignment with the **Ministry of Statistics & Programme Implementation (MoSPI)** and designed with an integration-ready architecture for the **iGOT Karmayogi** national capacity building ecosystem.

---

## 1. Problem Statement & Objective

In modern evidence-based governance, public officers must continuously upgrade their proficiencies across core statistical methodologies, modern programming (Python), data analytics, and survey design. Current training pathways often suffer from:
- Static, one-size-fits-all curricula without granular diagnostic competency scoring.
- Hidden proficiency gaps leading to flawed policy inferences.
- Lack of explainability behind recommended training interventions.
- Manual question authoring bottlenecks for training documents and manuals.

**SkillStat AI** solves this by delivering an end-to-end closed-loop learning engine:
1. **Diagnostic Competency Assessment**: Dynamically assesses 7 core statistical and technical competencies.
2. **Deterministic Skill Gap Engine**: Pinpoints discrepancies against the national 80% benchmark and assigns priority ratings (`HIGH`, `MEDIUM`, `LOW`).
3. **Transparent Explainable AI (XAI)**: Generates human-interpretable justifications explaining *why* courses were recommended.
4. **PDF Extraction & AI Question Authoring**: Parses uploaded training manuals via `pypdf` and synthesizes curriculum-grounded MCQs using LLMs (with smart offline Demo Mode fallback).
5. **Dynamic Competency Recalibration**: Evaluates quizzes and dynamically raises measured competency scores.
6. **iGOT Karmayogi Architecture**: Employs prototype abstraction layers conforming to DoPT national competency schemas.

---

## 2. Complete End-to-End Demo Flow

```text
LOGIN (demo / demo123)
   ↓
DASHBOARD (View baseline scores: Regression 35%, Visualization 40%, Python 45%)
   ↓
DIAGNOSTIC ASSESSMENT (Interactive 14-question psychometric evaluation)
   ↓
ASSESSMENT RESULT (Detailed score breakdown & answer explanations)
   ↓
SKILL GAP DETECTION (Regression: Gap 45 → HIGH, Python: Gap 35 → MEDIUM)
   ↓
PERSONALIZED RECOMMENDATIONS ("WHY THIS WAS RECOMMENDED" transparent XAI cards)
   ↓
LEARNING PATH (Ranked intervention sequence ordered by priority)
   ↓
UPLOAD LEARNING MATERIAL (PDF document upload with validation)
   ↓
EXTRACT PDF CONTENT (pypdf stream parsing, word count & error trapping)
   ↓
AI GENERATES MCQs (Structured JSON multiple choice questions with explanations)
   ↓
TAKE QUIZ (Interactive timed knowledge check)
   ↓
QUIZ RESULT (Pedagogical answer review & explanations)
   ↓
UPDATE COMPETENCY (Dynamic closed-loop score improvement: Before 35% → After 50%)
   ↓
PROGRESS DASHBOARD (Updated KPI cards, Chart.js bar and timeline charts)
```

---

## 3. Technology Stack

* **Backend**: Python 3.14 / Django 6.1, Django ORM, Django Authentication
* **Frontend**: Django Templates, HTML5, Vanilla CSS / Custom Design System, Bootstrap 5.3.3, Bootstrap Icons 1.11.3
* **Data Visualization**: Chart.js 4.4.2 (Live bar charts, gap radar charts, and progress timelines)
* **Document Processing**: `pypdf` 6.17 (PDF stream validation, encryption checking, text extraction)
* **AI Engine**: Structured LLM API integration layer (Google Gemini / OpenAI compatible) with resilient, domain-specific **Demo Mode** fallback
* **Database**: SQLite3 (zero-configuration development setup)

---

## 4. Project Architecture

```text
skillstat_ai/
│
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── README.md
│
├── config/                  # Django project root
│   ├── settings.py          # Settings, context processors, media & static config
│   ├── urls.py              # Root routing table
│   ├── context_processors.py# Global AI mode & platform context
│   └── wsgi.py
│
├── accounts/                # User authentication & officer profiles
│   ├── models.py            # UserProfile (Department, Cadre, Job Role)
│   ├── views.py             # Login, Register, Profile, Logout
│   └── forms.py
│
├── competency/              # Competency diagnostics & skill gap engine
│   ├── models.py            # Skill, UserCompetency, Assessment, Question, Attempt
│   ├── services.py          # CompetencyService (gap formula, assessment scoring)
│   └── management/commands/ # seed_demo_data command
│
├── learning/                # Personalized learning & explainable AI
│   ├── models.py            # Course, LearningMaterial, Recommendation
│   ├── services.py          # RecommendationService (XAI engine), IGOTIntegrationService
│   └── forms.py             # PDFUploadForm
│
├── quizzes/                 # Quiz authoring, taking, and competency updates
│   ├── models.py            # Quiz, QuizQuestion, QuizAttempt, QuizUserAnswer
│   ├── services.py          # QuizService (dynamic competency update formula)
│   └── views.py             # Quiz taking, evaluation, and review
│
├── ai_engine/               # AI service layer & document extraction
│   └── services.py          # PDFExtractionService (pypdf), AIService (Real/Mock LLM)
│
├── dashboard/               # Executive learner analytics & Chart.js visualizations
│   └── views.py             # Dashboard index, progress analytics, iGOT simulated sync
│
├── templates/               # Responsive Django Templates
│   ├── base.html
│   ├── partials/            # navbar.html, alerts.html
│   ├── accounts/            # login, register, profile
│   ├── dashboard/           # index, progress
│   ├── competency/          # assessment_take, assessment_result, skill_gaps
│   ├── learning/            # learning_path, course_list, course_detail, pdf_upload, etc.
│   └── quizzes/             # ai_generate, quiz_list, quiz_take, quiz_result
│
├── static/
│   └── css/custom.css       # Premium design system, typography & micro-interactions
└── media/
    └── materials/           # Uploaded PDF repository
```

---

## 5. Core Competency & Discrepancy Formula

### The 7 Canonical Competencies (MoSPI / Public Governance Framework):
1. **Statistics** (Benchmark: 80%)
2. **Python** (Benchmark: 80%)
3. **Data Analysis** (Benchmark: 80%)
4. **Data Visualization** (Benchmark: 80%)
5. **Regression** (Benchmark: 80%)
6. **Survey Methodology** (Benchmark: 80%)
7. **Statistical Interpretation** (Benchmark: 80%)

### Skill Gap Calculation:
$$\text{Gap} = \max(0, \text{Required Benchmark} - \text{Current Competency})$$

### Priority Classification:
* $\text{Gap} \ge 40 \implies \mathbf{HIGH\ PRIORITY}$ (Immediate training intervention)
* $\text{Gap} \ge 20 \implies \mathbf{MEDIUM\ PRIORITY}$ (Moderate skill deficit)
* $\text{Gap} < 20 \implies \mathbf{LOW\ PRIORITY}$ (Approaching target proficiency)

---

## 6. AI MCQ Generation & Resilient Demo Mode

### Strict Grounding Requirement
Questions generated by SkillStat AI are grounded in the provided document text or input excerpt. If the input text contains fewer than 30 words, generation is rejected with an informative error message:
> *"Not enough learning material to reliably generate questions. Please upload a document with more substantive text."*

### Two Execution Modes
1. **Real AI Mode (`AI_MODE=real`)**:
   Connects to an external LLM API (e.g. Gemini 1.5 Flash or OpenAI GPT-4o-mini). Requires `AI_API_KEY` in `.env`. Returns strictly validated JSON schemas.
2. **Demo Mode (`AI_MODE=mock`)**:
   Designed so the application **never fails** during an offline hackathon evaluation or presentation without an API key. Uses domain-specific statistical pattern extractors to synthesize questions directly relevant to the uploaded document. Clearly labeled in the UI as **`Demo Mode`**.

---

## 7. iGOT Karmayogi Integration Architecture

SkillStat AI implements `IGOTIntegrationService` (`learning/services.py`):
* **Data Mapping**: Standardizes internal skills to DoPT / MoSPI National Competency Dictionary codes (e.g., `Regression` $\rightarrow$ `COMP-STAT-009`, `Python` $\rightarrow$ `COMP-TECH-014`).
* **Protocol Ready**: Architected for REST / OAuth 2.0 mutual TLS (mTLS) national gateways.
* **Simulated Passbook Push**: Allows users to click **"Sync iGOT Passbook"** on the dashboard, dispatching payload representations to simulated 200 OK responses.

---

## 8. Installation & Setup

### Prerequisites
* Python 3.10+ (tested on Python 3.14)
* pip

### Quickstart Commands

```bash
# 1. Clone repository and navigate to directory
cd "skillStat AI"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment file
cp .env.example .env

# 4. Apply database migrations
python manage.py migrate

# 5. Populate pre-seeded demo dataset
python manage.py seed_demo_data

# 6. Run automated test suite
python manage.py test

# 7. Start the development server
python manage.py runserver
```

Open your browser and visit:
```text
http://127.0.0.1:8000/
```

---

## 9. Demo Credentials

A pre-configured demo account is included:
* **Username**: `demo`
* **Password**: `demo123`
* **Role**: Senior Statistical Officer / Data Analyst
* **Department**: Ministry of Statistics & Programme Implementation (MoSPI)
* **Staff/Admin Access**: Enabled (can access Django Admin at `/admin/`)

---

## 10. Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(Built-in)* | Django cryptographic signing key |
| `DEBUG` | `True` | Debug mode |
| `AI_MODE` | `mock` | `mock` for offline Demo Mode, `real` for live API |
| `AI_API_KEY` | `""` | Gemini or OpenAI API key (when using real mode) |
| `AI_MODEL` | `gemini-1.5-flash` | Model identifier |

---

## 11. Automated Testing

SkillStat AI includes 13 comprehensive Django unit and integration tests covering:
- Authentication, registration, and user profiles
- Competency scoring and overall average calculation
- Skill gap formula and priority thresholding
- Explainable AI recommendation generation
- iGOT Karmayogi integration schema mapping
- Quiz creation, scoring, and dynamic competency recalculation
- `pypdf` extraction and error trapping
- AI MCQ quality thresholds
- Full 12-step end-to-end integration walkthrough

Run all tests:
```bash
python manage.py test
```

---

## 12. Known Limitations & Future Work

* **Scanned Image PDFs**: `pypdf` extracts text streams; scanned raster images without OCR return a clean "empty document" status. Future releases can integrate Tesseract OCR.
* **Production iGOT Authorization**: Current iGOT integration operates as an architectural prototype layer until official NIC / DoPT client credentials are issued.
* **Multi-Language Support**: Future releases will incorporate localized translations in Hindi and regional languages for nationwide field enumerators.
