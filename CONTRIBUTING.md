# Contributing to ScriptToDoc

Thank you for your interest in contributing to ScriptToDoc! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive environment
- Report unacceptable behavior to project maintainers

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Azure subscription (for integration testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/scripttodoc.git
   cd scripttodoc
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env with your credentials
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local as needed
   ```

4. **Run Tests**
   ```bash
   # Backend
   cd backend
   pytest

   # Frontend
   cd frontend
   npm test
   ```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Examples:**
```bash
feat(backend): add semantic similarity scoring
fix(frontend): resolve progress bar animation bug
docs(setup): update Azure OpenAI configuration guide
test(pipeline): add integration tests for topic segmentation
```

### Code Style

#### Python (Backend)

- **PEP 8** style guide
- **Type hints** for all functions
- **Docstrings** for public APIs
- **Black** for formatting
- **flake8** for linting

```python
def process_transcript(
    transcript: str,
    config: PipelineConfig
) -> ProcessingResult:
    """
    Process a transcript and generate documentation.

    Args:
        transcript: Raw transcript text
        config: Pipeline configuration

    Returns:
        ProcessingResult with generated document

    Raises:
        ValueError: If transcript is empty
    """
    pass
```

#### TypeScript/React (Frontend)

- **ESLint** + **Prettier** configuration
- **Functional components** with hooks
- **TypeScript strict mode**
- **Descriptive variable names**

```typescript
interface JobStatus {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
}

export function StatusCard({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  // ...
}
```

### Testing Requirements

#### Backend Tests

All new features must include:

1. **Unit Tests** - Test individual functions
   ```python
   def test_parse_speaker_metadata():
       parser = TranscriptParser()
       result = parser.parse_metadata("Speaker 1: Hello")
       assert result.speaker == "Speaker 1"
       assert result.text == "Hello"
   ```

2. **Integration Tests** - Test component interactions
   ```python
   def test_pipeline_end_to_end():
       result = process_transcript_file(
           "sample.txt",
           config=test_config
       )
       assert result.success
       assert len(result.steps) > 0
   ```

3. **Coverage Target** - Maintain >80% coverage
   ```bash
   pytest --cov=script_to_doc --cov-report=html
   ```

#### Frontend Tests

1. **Component Tests** - Test UI components
   ```typescript
   test('renders progress tracker', () => {
     render(<ProgressTracker progress={0.5} />);
     expect(screen.getByText('50%')).toBeInTheDocument();
   });
   ```

2. **Integration Tests** - Test user flows
   ```typescript
   test('file upload flow', async () => {
     render(<UploadForm />);
     const file = new File(['content'], 'test.txt');
     // ...
   });
   ```

### Running Tests

```bash
# Backend - All tests
cd backend
pytest

# Backend - Specific test file
pytest tests/unit/test_parser.py

# Backend - With coverage
pytest --cov=script_to_doc

# Frontend - All tests
cd frontend
npm test

# Frontend - Watch mode
npm test -- --watch

# Frontend - Coverage
npm test -- --coverage
```

## Pull Request Process

### Before Submitting

1. **Update Documentation**
   - Update relevant README files
   - Add docstrings to new functions
   - Update API documentation if needed

2. **Run Tests**
   - All tests must pass
   - Add tests for new functionality
   - Maintain or improve coverage

3. **Code Quality**
   - Run linters (flake8, ESLint)
   - Format code (Black, Prettier)
   - Fix any warnings

4. **Security Check**
   - No secrets in code
   - Input validation added
   - Dependencies audited

### Submitting a Pull Request

1. **Push Your Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use descriptive title
   - Reference related issues
   - Describe changes made
   - Include screenshots if UI changes

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing performed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings
   - [ ] Tests pass locally
   ```

4. **Review Process**
   - Address reviewer comments
   - Keep PR focused and small
   - Be responsive to feedback
   - Update branch if main changes

### PR Requirements

- ✅ All tests passing
- ✅ Code review approved
- ✅ No merge conflicts
- ✅ Documentation updated
- ✅ Changelog updated (if applicable)

## Development Guidelines

### Adding New Features

1. **Plan First**
   - Discuss in issue or discussion
   - Get feedback on approach
   - Consider alternatives

2. **Implement Incrementally**
   - Start with tests
   - Implement core functionality
   - Add error handling
   - Write documentation

3. **Follow Patterns**
   - Use existing code as reference
   - Maintain consistency
   - Avoid reinventing wheels

### Fixing Bugs

1. **Reproduce the Bug**
   - Create failing test
   - Document steps to reproduce
   - Identify root cause

2. **Fix and Verify**
   - Make minimal changes
   - Ensure test passes
   - Check for regressions
   - Document the fix

### Refactoring

1. **Ensure Test Coverage**
   - Write tests first if missing
   - Run tests before changes
   - Run tests after changes

2. **Small Changes**
   - One refactoring per PR
   - Maintain functionality
   - Document breaking changes

## Project Structure

### Backend

```
backend/
├── api/              # FastAPI endpoints
├── script_to_doc/    # Core processing library
│   ├── pipeline.py          # Main orchestration
│   ├── transcript_parser.py # Parsing logic
│   ├── topic_segmenter.py   # Segmentation
│   └── ...
├── workers/          # Background processors
├── tests/            # Test suite
│   ├── unit/        # Unit tests
│   ├── integration/ # Integration tests
│   └── e2e/         # End-to-end tests
└── scripts/         # Utility scripts
```

### Frontend

```
frontend/
├── app/              # Next.js pages
├── components/       # React components
├── lib/              # Utilities and API
└── public/           # Static assets
```

## Documentation

### Types of Documentation

1. **Code Comments**
   - Explain "why", not "what"
   - Document complex logic
   - Add TODOs for future work

2. **API Documentation**
   - FastAPI auto-generates docs
   - Add descriptions to endpoints
   - Document request/response models

3. **User Guides**
   - Located in `docs/guides/`
   - Step-by-step instructions
   - Include examples

4. **Architecture Docs**
   - Located in `docs/architecture/`
   - System design decisions
   - Technical specifications

### Updating Documentation

- Update READMEs when adding features
- Add examples for new APIs
- Update architecture docs for major changes
- Keep changelog current

## Communication

### Asking Questions

- Check existing documentation first
- Search closed issues
- Ask in discussions
- Be specific and provide context

### Reporting Bugs

Use the bug report template:
- Describe the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Environment details

### Suggesting Features

Use the feature request template:
- Describe the feature
- Use case / problem it solves
- Proposed solution
- Alternatives considered

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH
- MAJOR - Breaking changes
- MINOR - New features (backward compatible)
- PATCH - Bug fixes

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tag created
- [ ] Deployed to staging
- [ ] Smoke tests passed
- [ ] Deployed to production

## Resources

### Documentation
- [Project README](README.md)
- [Architecture Guide](docs/architecture/README.md)
- [Setup Guide](docs/setup/AZURE_SERVICES_SETUP_GUIDE.md)
- [API Documentation](http://localhost:8000/docs)

### Tools
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Pytest](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)

### Learning
- [Azure Documentation](https://docs.microsoft.com/azure/)
- [Python Best Practices](https://docs.python-guide.org/)
- [React Best Practices](https://react.dev/)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to ScriptToDoc!

---

**Questions?** Open a discussion or contact the maintainers.
