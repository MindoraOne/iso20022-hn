# pain001 Product Roadmap & Backlog

## Mission
Deliver a robust, high-performance ISO 20022 payment library with:
- Full pain.001 format support (v03–v12+)
- Streaming/batch processing for large datasets
- REST API for enterprise integration
- CLI for user-friendly interactions

## Context & Background
pain001 is a mature Python library for automating ISO 20022-compliant payment files from CSV/SQLite data. Current state:
- **v0.0.43**: Released with PyPI authentication fix
- **Coverage**: 98.57%, 341 passing tests, Pylint 10.00/10
- **Supported formats**: pain.001.001.03–11

## Strategic Goals

### v0.0.44–0.0.46 (Q1 2026)
**Focus**: Core capability expansion + UX improvements
- #104 Add pain.001.001.12 (CustomerCreditTransferInitiationV12)
- #78 End-to-end streaming pipeline with chunked reads/writes
- #105 Make CLI interface more intuitive
- #106 Expose API endpoints for pain001 operations
- #107 Preset profiles for banks/regions (SEPA)
- #103 Lightweight metrics hooks
- #102 Structured logging normalization
- #100 Schema evolution guardrails
- #95 Performance playbook for large files

**Impact**: Enterprise-ready streaming, new format support, programmatic access.

### v0.0.47–0.0.48 (Q2 2026)
**Focus**: Architecture hardening + performance optimization
- #76 Refactor XML message prep into registry-driven pipeline
- #77 Introduce typed payment models with required-field validation
- #80 Split process_files into focused helpers
- #81 Add CLI dry-run/validate-only mode with structured errors
- #79 Cache Jinja2 templates and XSD schemas per run
- #87 Lazy/streaming CSV and DB loaders
- #88 Measure and optimize large-batch XML generation
- #82 CLI/Library parity tests
- #83 Harden template loading and sandbox Jinja2
- #84 Strengthen XSD validation error reporting and cache

**Impact**: Cleaner codebase, better performance, reduced maintenance burden.

### v0.0.49+ (Q3 2026+)
**Focus**: Testing coverage + observability + advanced features
- #90 Golden-file tests for each pain.001 version
- #92 Mutation testing coverage review
- #91 Property-based tests on payment rows
- #94 Troubleshooting guide for schema/template/data errors
- #93 Add validate-only and streaming usage docs
- #98 Release workflow hardening follow-up
- #86 File path safety audit
- #85 Input sanitization for CSV/DB ingestion
- #96 Automated issue templates for features/bugs
- #97 Add lint/type/test pre-push hook (optional)
- #89 Optional async-ready adapters (exploratory)
- #108 Batch job runner with progress reporting
- #109 Validation-only web hook / callback support
- #110 Packaging: publish official Docker image

**Impact**: Production-grade reliability, deployment options, enterprise readiness.

## Developer Onboarding

### Getting Started
1. **Read the docs**: [README.md](README.md) for project overview
2. **Set up environment**: Follow [CONTRIBUTING.md](CONTRIBUTING.md)
3. **Run quality gates**: `make format && make lint && make type && make test` (mandatory pre-commit)

### Picking an Issue
- Look for labels: `priority/p0` (critical), `priority/p1` (high), `good first issue`
- Check the milestone: v0.0.44–0.0.46 is the current focus
- Review the issue description for acceptance criteria and technical notes

### Pull Request Workflow
1. Fork the repo
2. Create a feature branch: `git checkout -b feature/issue-NNN`
3. Make changes and run the quality gate
4. Push and open a PR (link to the issue)
5. Code review + CI checks
6. Merge once approved

## Key Metrics
- **Test Coverage**: 98.57% (target: ≥95%)
- **Code Quality**: Pylint 10.00/10 (0 warnings)
- **Build Status**: All checks pass (ruff, flake8, mypy, pytest)
- **Release Cadence**: ~2 weeks
- **Total Backlog**: 43 open issues across 3 milestones

## Commands & Workflows

### Local Quality Gate (Required Before Commit)
```bash
make format    # Black, isort, ruff
make lint      # Pylint, flake8, ruff
make type      # MyPy
make test      # Pytest with coverage
```

### Documentation
```bash
make docs      # Build Sphinx docs locally
```

### Performance Testing
```bash
make perf      # Run benchmarks
make mutate    # Run mutation testing
```

## Contact & Questions
- **Issues**: Use GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

*Last updated: 2026-01-11*
*Roadmap valid through v0.0.49+*
