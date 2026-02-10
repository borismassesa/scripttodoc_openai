# 📁 File Organization & Structure

This document describes the organized file structure of the ScriptToDoc project.

---

## 🎯 Organization Principles

1. **Root Level** - Only essential project files (README, QUICK_START, CONTRIBUTING, SECURITY)
2. **docs/** - All documentation organized by category
3. **backend/** - Backend application code
4. **frontend/** - Frontend application code
5. **deployment/** - Deployment configurations

---

## 📂 Current Structure

```
ScriptToDoc/
├── README.md                           # Main project documentation
├── QUICK_START.md                      # Quick start guide (convenience)
├── CONTRIBUTING.md                     # Contribution guidelines
├── SECURITY.md                         # Security policy
├── .gitignore                          # Git ignore rules
├── .dockerignore                       # Docker ignore rules
│
├── backend/                            # Backend application
│   ├── api/                            # FastAPI application
│   │   ├── main.py                     # API entry point
│   │   ├── routes/                     # API endpoints
│   │   ├── models.py                   # Data models
│   │   └── dependencies.py             # Dependency injection
│   │
│   ├── script_to_doc/                  # Core processing pipeline
│   │   ├── pipeline.py                 # Main processing pipeline
│   │   ├── azure_openai_client.py      # OpenAI integration (async + sync)
│   │   ├── knowledge_fetcher.py        # URL fetching (async + sync)
│   │   ├── document_generator.py       # Document generation
│   │   ├── topic_segmenter.py          # Topic segmentation
│   │   ├── transcript_cleaner.py       # Transcript cleaning
│   │   ├── local_db.py                 # SQLite client
│   │   ├── local_storage.py            # Filesystem client
│   │   └── converters/                 # Document conversion
│   │
│   ├── tests/                          # Test suite
│   │   ├── unit/                       # Unit tests
│   │   ├── integration/                # Integration tests
│   │   └── e2e/                        # End-to-end tests
│   │
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile                      # Docker configuration
│   ├── .env.template                   # Environment template
│   └── sample_transcript.txt           # Sample input
│
├── frontend/                           # Frontend application
│   ├── app/                            # Next.js pages
│   ├── components/                     # React components
│   ├── lib/                            # Utility functions
│   ├── public/                         # Static assets
│   ├── package.json                    # Node dependencies
│   ├── Dockerfile                      # Docker configuration
│   └── next.config.ts                  # Next.js config
│
├── deployment/                         # Deployment configurations
│   ├── docker-compose.yml              # Docker Compose
│   └── kubernetes/                     # K8s manifests (if applicable)
│
└── docs/                               # Documentation (organized)
    ├── README.md                       # Documentation index
    │
    ├── deployment/                     # Deployment docs
    │   ├── README.md
    │   ├── PRODUCTION_DEPLOYMENT.md
    │   ├── PRODUCTION_DEPLOYMENT_PLAN.md
    │   ├── PRODUCTION_DEPLOYMENT_PLAN_AZURE_FRONTEND.md
    │   └── HOSTING_COST_SUMMARY.md
    │
    ├── performance/                    # Performance docs
    │   ├── README.md
    │   ├── PERFORMANCE_IMPROVEMENTS.md
    │   └── PERFORMANCE_OPTIMIZATION_SUMMARY.md
    │
    ├── migration/                      # Migration docs
    │   ├── README.md
    │   └── MIGRATION_COMPLETE.md
    │
    ├── bug-fixes/                      # Bug fix docs
    │   ├── README.md
    │   ├── AI_TITLE_GENERATION_FIX.md
    │   └── CRITICAL_FIX_STEP_COUNT.md
    │
    ├── analysis/                       # Technical analysis
    │   ├── AGENT_ARCHITECTURE.md
    │   ├── FILE_CONVERSION_IMPLEMENTATION_PLAN.md
    │   ├── IMPLEMENTATION_GAP_ANALYSIS.md
    │   ├── INTELLIGENT_KNOWLEDGE_INTEGRATION.md
    │   ├── KNOWLEDGE_SOURCES_STATUS_REPORT.md
    │   ├── PROMPT_ANALYSIS.md
    │   ├── HOSTING_COST_ANALYSIS.md
    │   ├── ARCHITECTURE_DIAGRAM_MERMAID.md
    │   └── ...
    │
    ├── architecture/                   # System architecture
    │   ├── 1_SYSTEM_ARCHITECTURE.md
    │   ├── 2_IMPLEMENTATION_PHASES.md
    │   ├── 3_USER_JOURNEY.md
    │   ├── 4_DATA_FLOW.md
    │   ├── 5_VISUAL_FLOWCHARTS.md
    │   ├── 6_TECHNOLOGY_DECISIONS.md
    │   ├── DOCUMENT_STRUCTURE.md
    │   └── ...
    │
    ├── phases/                         # Phase completion docs
    │   ├── PHASE1_COMPLETE.md
    │   ├── PHASE1_MVP_STATUS.md
    │   ├── PHASE1_IMPLEMENTATION_PLAN.md
    │   ├── PHASE2_COMPLETE.md
    │   └── ...
    │
    ├── setup/                          # Setup guides
    │   ├── AZURE_SERVICES_SETUP_GUIDE.md
    │   ├── AZURE_OPENAI_SETUP.md
    │   ├── FILE_CONVERSION_SETUP_GUIDE.md
    │   ├── COSMOS_DB_INDEXING_OPTIMIZATION.md
    │   └── DEPLOYMENT_CHECKLIST.md
    │
    ├── guides/                         # User guides
    │   ├── FRONTEND_QUICKSTART.md
    │   ├── FRONTEND_COMPLETE.md
    │   └── PIPELINE_USAGE_GUIDE.md
    │
    └── ux-design/                      # UX design docs
        └── (design documents)
```

---

## 🗂️ Documentation Categories

### 📚 Core Documentation (Root Level)
Essential files that developers need immediately:
- **README.md** - Project overview, features, and quick links
- **QUICK_START.md** - Get running in 5 minutes
- **CONTRIBUTING.md** - How to contribute
- **SECURITY.md** - Security policy and vulnerability reporting

### 🚢 Deployment Documentation
Everything related to deploying to production:
- Production deployment guides
- Azure deployment plans
- Hosting cost analysis
- Deployment checklists

### ⚡ Performance Documentation
Performance optimizations and benchmarks:
- Latest performance improvements (4x faster!)
- Optimization techniques
- Benchmark results
- Performance tuning guides

### 🔄 Migration Documentation
Major architectural changes:
- Azure to Local migration
- Service migrations
- Breaking changes
- Migration guides

### 🐛 Bug Fixes Documentation
Critical issues and their resolutions:
- Bug descriptions
- Root cause analysis
- Fix implementation
- Prevention strategies

### 🏗️ Architecture Documentation
System design and architecture:
- System architecture diagrams
- Data flow diagrams
- Technology decisions
- Design patterns

### 📊 Phase Documentation
Development phase completion reports:
- Phase 1: Intelligent parsing
- Phase 2: Advanced features
- Implementation plans
- Status reports

### 🔧 Setup Documentation
Configuration and setup guides:
- Azure services setup
- OpenAI configuration
- Database setup
- Deployment checklists

### 📖 User Guides
End-user and developer guides:
- Quick start guides
- Feature guides
- API usage
- Pipeline usage

### 🔍 Analysis Documentation
Technical analysis and research:
- Feature analysis
- Implementation gap analysis
- Cost analysis
- Technical investigations

---

## 🎯 Navigation Strategies

### For New Developers
1. Start with [README.md](README.md)
2. Follow [QUICK_START.md](QUICK_START.md)
3. Read [docs/architecture/1_SYSTEM_ARCHITECTURE.md](docs/architecture/1_SYSTEM_ARCHITECTURE.md)

### For DevOps Engineers
1. Check [docs/deployment/](docs/deployment/)
2. Review [docs/setup/DEPLOYMENT_CHECKLIST.md](docs/setup/DEPLOYMENT_CHECKLIST.md)
3. See [docs/deployment/HOSTING_COST_SUMMARY.md](docs/deployment/HOSTING_COST_SUMMARY.md)

### For Product Managers
1. Read [docs/architecture/3_USER_JOURNEY.md](docs/architecture/3_USER_JOURNEY.md)
2. Check [docs/phases/](docs/phases/)
3. Review feature status in phase docs

### For Performance Engineers
1. Start with [docs/performance/PERFORMANCE_IMPROVEMENTS.md](docs/performance/PERFORMANCE_IMPROVEMENTS.md)
2. Review optimization techniques
3. Check benchmark results

---

## 📋 Maintenance

### Adding New Documentation
1. Determine the appropriate category
2. Create the file in the correct subdirectory
3. Add an entry to the subdirectory's README.md
4. Update [docs/README.md](docs/README.md) if it's a major addition

### Moving Files
1. Use `git mv` to preserve history
2. Update all internal links
3. Update README files
4. Test all links work

### Removing Old Documentation
1. Check for references to the document
2. Update or remove links
3. Archive if historically important
4. Delete if truly obsolete

---

## ✨ Benefits of This Organization

✅ **Clear Structure** - Easy to find what you need
✅ **Scalable** - Can grow with the project
✅ **Discoverable** - Each folder has a README
✅ **Maintainable** - Clear ownership and categories
✅ **Professional** - Industry-standard organization
✅ **Git-Friendly** - Clean git status and history

---

**Organized:** February 10, 2026
**Maintainer:** Development Team
