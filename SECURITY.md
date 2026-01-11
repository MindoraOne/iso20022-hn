# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in pain001, please email **security@pain001.com** instead of using the issue tracker.

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide updates on remediation timeline.

## Security Standards

Pain001 adheres to OWASP Top 10 prevention practices:
- **Input Validation**: All untrusted inputs validated for type, length, format, range
- **Secrets Protection**: No credentials hardcoded; environment variables required
- **XXE Prevention**: Uses `defusedxml` exclusively, never `xml.etree.ElementTree`
- **SQL Protection**: Parameterized queries used; no string formatting
- **Deserialization**: JSON only for untrusted data; never `pickle`
- **Network Security**: TLS verification mandatory; explicit timeouts on all requests
- **Cryptography**: AES-256, SHA-256+, bcrypt/argon2 for passwords

## Dependency Security

- Weekly Dependabot scans for CVEs
- Security updates prioritized: critical (7 days), high (30 days), medium (60 days)
- Transitive dependency auditing with `poetry show --tree`
- SBOM generation via CycloneDX for supply chain transparency

## Continuous Integration

- PR gate runs: ruff, black, mypy, pytest on every PR
- Nightly heavy validation: full `make check` including flake8, pylint, bandit
- Daily security scanning: CVE detection, license compliance, SBOM generation
- Coverage requirements: 95% minimum, 98%+ target

## Codecov Setup

The project uses Codecov for coverage tracking. To enable Codecov in your fork:

1. Visit https://codecov.io and sign in with your GitHub account
2. Enable coverage for the pain001 repository
3. Codecov will automatically detect coverage.xml uploads from GitHub Actions
4. Coverage badge will appear once first upload is processed

**Note**: The Codecov token (`AaUxKfRiou`) is stored in the badge URL for public repositories. For private repos, use GitHub Secrets:

```bash
# In GitHub Settings → Secrets → New repository secret
CODECOV_TOKEN=<your-codecov-token>
```

## Contact

- **Email**: security@pain001.com
- **GitHub Issues**: https://github.com/sebastienrousseau/pain001/security/advisories
- **GitHub Discussions**: https://github.com/sebastienrousseau/pain001/discussions
