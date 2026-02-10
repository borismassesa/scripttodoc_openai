# ScriptToDoc - AI-Powered Training Document Generator

> **Transform meeting transcripts and training videos into professional, citation-backed training documents using Azure AI services.**

[![Azure](https://img.shields.io/badge/Azure-100%25%20Native-0078D4?logo=microsoft-azure)](https://azure.microsoft.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?logo=next.js)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Documentation](#project-documentation)
- [Quick Start](#quick-start)
- [Technology Stack](#technology-stack)
- [Project Status](#project-status)
- [Team](#team)

---

## Overview

**ScriptToDoc** is an intelligent document generation system that converts meeting transcripts, screenshots, and training videos into professional step-by-step training documents. Every generated step is grounded in source material with confidence scoring to prevent AI hallucination.

### The Problem

Training coordinators spend **2-4 hours** manually creating training documents from:
- 📝 Meeting transcripts (messy, with filler words and timestamps)
- 📸 Screenshots (scattered across different folders)
- 🎥 Training videos (need to be watched and documented manually)

### The Solution

**ScriptToDoc automates this process in ~20 seconds**, generating:
- ✅ Clean, professional Word documents
- ✅ Step-by-step instructions with confidence scores
- ✅ Source citations (transcript excerpts, screenshot references)
- ✅ Visual references linked to specific actions

### Example Transformation

**Input (Raw Transcript):**
```
[00:15:32] Speaker 1: Um, so like, first you need to, you know, open the Azure portal. [laughs]
[00:16:05] Speaker 2: Yeah, and then, uh, navigate to resource groups...
```

**Output (Professional Document):**
```
TRAINING DOCUMENT: Azure Portal Navigation

Step 1: Access the Azure Portal
Overview: Navigate to portal.azure.com and authenticate with your credentials

Key Actions:
  • Open web browser
  • Navigate to portal.azure.com
  • Enter credentials and sign in

[Confidence: High (0.92) | Sources: transcript (sentence 5), visual (screenshot_01.png)]

[Reference Section with full transcript excerpts and citations]
```

---

## Key Features

### 🎯 Core Capabilities

#### 1. **Intelligent Transcript Processing**
- Remove timestamps, filler words, and speaker labels
- Clean WEBVTT/SRT format artifacts
- Sentence tokenization and normalization
- Azure Document Intelligence structure extraction

#### 2. **Visual Content Analysis**
- Screenshot OCR with Azure DI (prebuilt-layout model)
- UI element extraction (buttons, menus, forms)
- Table detection and extraction
- Cross-reference with transcript content

#### 3. **Source Grounding System** (Anti-Hallucination)
- Every step backed by source references
- Multi-factor confidence scoring (0.0-1.0)
- Cross-validation between transcript and visuals
- Quality thresholds (reject steps with confidence < 0.7)

#### 4. **Professional Document Generation**
- Word (.docx) format with python-docx
- Structured steps with actions, prerequisites, expected results
- Citation system with confidence indicators
- Appendix with full source references

### 🚀 Advanced Features

#### 5. **Video Processing** (Phase 3)
- Audio extraction and transcription (Azure Speech-to-Text)
- Key frame extraction (scene change detection)
- Temporal alignment (timestamps → sentences → frames)
- Full end-to-end pipeline

#### 6. **Adaptive Processing**
- Smart step count suggestions (LLM analyzes complexity)
- Fallback strategies (Azure DI → OpenAI → NLTK)
- Graceful degradation on service failures
- Configurable quality vs. speed trade-offs

#### 7. **Enterprise Features**
- Azure AD B2C authentication (SSO)
- Role-based access control (RBAC)
- Audit logging and compliance
- Cost tracking and optimization

---

## Architecture

### High-Level System Design

```
┌──────────────┐
│    User      │
│  (Browser)   │
└──────┬───────┘
       │ HTTPS
       ▼
┌──────────────────┐       ┌─────────────────┐
│  Next.js Frontend │       │  FastAPI Backend│
│  (Static Web App) │◄─────►│ (Container Apps)│
└──────────────────┘       └────────┬─────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     │              │              │
                     ▼              ▼              ▼
            ┌────────────┐  ┌─────────────┐  ┌──────────┐
            │ Cosmos DB  │  │ Service Bus │  │  Blob    │
            │ (Job State)│  │  (Queue)    │  │ Storage  │
            └────────────┘  └──────┬──────┘  └──────────┘
                                   │
                                   │ Trigger
                                   ▼
                         ┌──────────────────┐
                         │ Background Worker│
                         │ (Container Apps) │
                         └─────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌──────────────┐  ┌─────────┐  ┌──────────┐
            │  Azure DI    │  │ Azure   │  │ Computer │
            │ (Structure)  │  │ OpenAI  │  │ Vision   │
            └──────────────┘  └─────────┘  └──────────┘
```

### Processing Pipeline

```
Transcript → Clean → Azure DI → Build Sources → Generate Steps → Validate → Create Doc → Upload
    1s         1s       3s           1s              8s           1s         1s        1s
                                                                                  
Total: ~15-20 seconds
```

---

## Project Documentation

This project includes comprehensive planning documentation:

### 📘 Planning Documents

| Document | Description |
|----------|-------------|
| **[1_SYSTEM_ARCHITECTURE.md](./1_SYSTEM_ARCHITECTURE.md)** | Detailed Azure architecture, services breakdown, security model |
| **[2_IMPLEMENTATION_PHASES.md](./2_IMPLEMENTATION_PHASES.md)** | 8-week roadmap from foundation to production |
| **[3_USER_JOURNEY.md](./3_USER_JOURNEY.md)** | User flows for all three scenarios (transcript, +screenshots, video) |
| **[4_DATA_FLOW.md](./4_DATA_FLOW.md)** | Data schemas, state transitions, storage patterns |
| **[5_VISUAL_FLOWCHARTS.md](./5_VISUAL_FLOWCHARTS.md)** | ASCII flowcharts, decision trees, visual diagrams |
| **[6_TECHNOLOGY_DECISIONS.md](./6_TECHNOLOGY_DECISIONS.md)** | Technology choices, alternatives, trade-offs |

### 📊 Key Diagrams

- [System Architecture](./1_SYSTEM_ARCHITECTURE.md#high-level-architecture)
- [Processing Pipeline](./5_VISUAL_FLOWCHARTS.md#2-processing-pipeline-flow)
- [Source Reference System](./5_VISUAL_FLOWCHARTS.md#3-source-reference-system)
- [User Journey Map](./5_VISUAL_FLOWCHARTS.md#5-user-journey-map)
- [Error Handling Flow](./5_VISUAL_FLOWCHARTS.md#6-error-handling-flow)

---

## Quick Start

> ⚠️ **Project Status:** Currently in planning phase. Implementation starts after requirements review.

### Prerequisites

**Azure Resources:**
- Azure subscription with contributor access
- Azure Document Intelligence resource
- Azure OpenAI Service access (requires application approval)
- Azure Container Apps environment
- Azure Cosmos DB account
- Azure Storage account
- Azure Service Bus namespace

**Development Environment:**
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Azure CLI
- VS Code (recommended)

### Installation (When Implementation Begins)

```bash
# 1. Clone repository
git clone https://github.com/yourorg/scripttodoc.git
cd scripttodoc

# 2. Set up Azure resources
cd infrastructure/bicep
az deployment group create \
  --resource-group rg-scripttodoc-dev \
  --template-file main.bicep

# 3. Configure environment
cp .env.template .env
# Edit .env with Azure resource endpoints and keys

# 4. Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 5. Install frontend dependencies
cd ../frontend/transcript-trainer-ui
npm install

# 6. Run locally
# Terminal 1 - Backend
cd backend
uvicorn api.main:app --reload

# Terminal 2 - Worker
cd backend
python workers/processor.py

# Terminal 3 - Frontend
cd frontend/transcript-trainer-ui
npm run dev
```

### Usage Example

```python
from script_to_doc.pipeline import PipelineConfig, process_transcript

# Configure pipeline
config = PipelineConfig(
    use_azure_di=True,
    use_openai=True,
    min_steps=5,
    target_steps=10,
    tone="Professional",
    audience="Technical Users"
)

# Process transcript
result = process_transcript(
    transcript_path="meeting_transcript.txt",
    output_dir="./output",
    config=config,
    screenshots=["screen1.png", "screen2.png"]
)

print(f"Document created: {result['document_path']}")
print(f"Confidence: {result['metrics']['average_confidence']:.2f}")
```

---

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework with async support
- **Azure Document Intelligence** - Structure extraction and OCR
- **Azure OpenAI Service** - GPT-4o-mini for content generation
- **python-docx** - Word document generation
- **Pydantic** - Data validation and type safety
- **NLTK** - Natural language processing (fallback)

### Frontend
- **Next.js 13+** - React framework with SSR
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **React Query** - Data fetching and caching

### Infrastructure
- **Azure Container Apps** - Serverless container hosting
- **Azure Cosmos DB** - NoSQL database (serverless mode)
- **Azure Blob Storage** - File storage with lifecycle policies
- **Azure Service Bus** - Reliable message queue
- **Azure Key Vault** - Secrets management
- **Application Insights** - Monitoring and telemetry
- **Azure Static Web Apps** - Frontend hosting with CDN

### Security
- **Azure AD B2C** - Authentication and SSO
- **Azure Front Door + WAF** - DDoS protection and rate limiting
- **Managed Identity** - Credential-less Azure service access
- **Private Endpoints** - Network isolation (optional)

---

## Project Status

### Current Phase: **Planning & Architecture** ✅

- [x] Complete project specification
- [x] System architecture design
- [x] Implementation phases breakdown
- [x] User journey mapping
- [x] Data flow design
- [x] Technology decisions documented
- [ ] Azure resources provisioned
- [ ] Development environment setup
- [ ] Core pipeline implementation

### Upcoming Phases

**Phase 0: Foundation (Week 1)**
- Provision Azure resources with IaC (Bicep)
- Set up CI/CD pipeline (GitHub Actions)
- Configure development environment

**Phase 1: Core MVP (Weeks 2-3)**
- Basic transcript processing
- Azure DI + OpenAI integration
- Source reference system
- Word document generation
- REST API with job queue

**Phase 2: Enhanced (Week 4)**
- Screenshot analysis
- Visual cross-referencing
- Enhanced confidence scoring

**Phase 3: Advanced (Weeks 5-6)**
- Video frame extraction
- Speech-to-text transcription
- Temporal alignment

**Phase 4: Frontend (Week 7)**
- Next.js UI with upload interface
- Real-time progress tracking
- Document preview and download

**Phase 5: Production (Week 8)**
- Security hardening
- Monitoring dashboards
- Performance optimization
- Documentation and training

---

## Success Metrics

### Quality Targets
- ✅ **Confidence:** 80%+ average across all steps
- ✅ **Source Coverage:** 95%+ steps with source backing
- ✅ **Accuracy:** 90%+ correctness (manual review)
- ✅ **Rejection Rate:** <10% steps rejected for low confidence

### Performance Targets
- ✅ **Processing Time:** <20s for basic transcript (500 words)
- ✅ **API Response:** <200ms for status checks
- ✅ **Uptime:** 99%+ availability
- ✅ **Cost:** <$0.50 per basic document

### User Experience Targets
- ✅ **Upload Success:** 99%+ successful uploads
- ✅ **Time Savings:** 2-4 hours → 20 seconds (600x faster)
- ✅ **User Satisfaction:** 4.5+/5.0 rating

---

## Cost Estimate

### Monthly Costs (100 jobs/day, ~3000 jobs/month)

| Service | Cost | Percentage |
|---------|------|------------|
| Azure OpenAI | $150 | 50% |
| Azure Container Apps | $75 | 25% |
| Azure Document Intelligence | $30 | 10% |
| Cosmos DB | $25 | 8% |
| Blob Storage | $15 | 5% |
| Other (Service Bus, Key Vault, Insights) | $5 | 2% |
| **Total** | **~$300/month** | **100%** |

**Per-Job Cost:** ~$0.10

### Cost Optimization
- ✅ Scale to zero when idle (Container Apps)
- ✅ Cache Azure DI results (24h TTL) - saves 30%
- ✅ Use GPT-4o-mini instead of GPT-4 - saves 90%
- ✅ Lifecycle policies on storage - saves 20%

---

## Team

**Lead AI Agent Engineer:** Boris
- Project lead and architect
- Responsible for MVP delivery

**Target Audience:**
- Training coordinators
- Documentation teams
- L&D (Learning & Development) professionals
- Technical writers

**Stakeholders:**
- Microsoft ecosystem users
- Enterprise clients requiring Azure-native solutions

---

## Development Roadmap

```
Week 1  │ ████████░░░░░░░░░░░░░░░░░░░░░░░░ │ Foundation & Setup
Week 2  │ ░░░░░░░░████████░░░░░░░░░░░░░░░░ │ Core Pipeline (Part 1)
Week 3  │ ░░░░░░░░░░░░░░░░████████░░░░░░░░ │ Core Pipeline (Part 2)
Week 4  │ ░░░░░░░░░░░░░░░░░░░░░░░░████████ │ Screenshot Features
Week 5  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ Video Processing (Part 1)
Week 6  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ Video Processing (Part 2)
Week 7  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ Frontend UI
Week 8  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ Production Ready
```

**Timeline:** 8 weeks to production-ready MVP

---

## Key Differentiators

What makes ScriptToDoc unique:

1. **🎯 Source Grounding** - Every step backed by verifiable sources (prevents hallucination)
2. **📊 Confidence Scoring** - Transparent quality metrics for each generated step
3. **🔄 Hybrid Approach** - Azure DI (structure) + OpenAI (content) + NLTK (fallback)
4. **📸 Visual Intelligence** - Screenshots become actionable references
5. **📚 Citation System** - Professional references like academic papers
6. **🎚️ Adaptive Quality** - Smart step counts and quality thresholds
7. **☁️ 100% Azure** - Seamless Microsoft ecosystem integration

---

## License

**Proprietary** - All rights reserved. This project is developed for internal use within Microsoft ecosystem clients.

---

## Support & Contact

**Documentation:** See [docs/](./docs/) folder for detailed guides

**Issues:** (To be set up after implementation begins)

**Questions:** Contact project lead

---

## Acknowledgments

**Technologies:**
- Azure AI Services team for excellent APIs
- FastAPI framework for developer experience
- Next.js team for modern web development
- Open-source community for supporting libraries

---

## Next Steps

### For Stakeholders
1. Review [System Architecture](./1_SYSTEM_ARCHITECTURE.md)
2. Review [Implementation Phases](./2_IMPLEMENTATION_PHASES.md)
3. Provide feedback on requirements
4. Approve Azure resource budget (~$300/month)
5. Approve timeline (8 weeks to MVP)

### For Development Team (When Approved)
1. Provision Azure resources ([Phase 0](./2_IMPLEMENTATION_PHASES.md#phase-0-foundation--azure-setup-week-1))
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews

---

**Built with ❤️ for the Microsoft Ecosystem**

*Last Updated: November 3, 2025*

