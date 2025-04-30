# Unique Rules from 003-important.md

## Core Rules

### 1. Type Safety & Data Validation
- Use Pydantic V2 for all data validation
- Enforce strict type hinting
- Ban `typing.Any`
- Use `@pydantic.validate_arguments` where needed
- Enable strict mypy checking

### 2. LangChain Architecture
- Organize into dedicated directories:
  - `src/agents/`
  - `src/chains/`
  - `src/tools/`
  - `src/prompts/`
  - `src/parsers/`
- Use LCEL for chain composition
- Implement proper memory management
- Define clear tool schemas

### 3. Cloud Security
- Follow least privilege principle
- Use AWS Secrets Manager
- Enable encryption at rest
- Use VPC endpoints
- Validate all inputs
- Keep dependencies updated

### 4. API Standards
- Use standardized response structure
- Apply semantic HTTP status codes
- Generate OpenAPI documentation
- Version APIs appropriately

### 5. Dependency Management
- Use poetry or pip-tools
- Review dependencies carefully
- Audit for vulnerabilities
- Keep dependencies updated

### 6. Testing Strategy
- Unit tests with pytest
- Integration tests
- LangChain-specific tests
- Optional E2E tests
- CI integration

### 7. Documentation
- Use Google-style docstrings
- Maintain comprehensive README
- Create architecture diagrams
- Document configurations
- Provide AI context

### 8. Performance Optimization
- Use async/await
- Optimize Lambda settings
- Implement caching
- Optimize database queries
- Monitor performance

### 9. Error Handling & Logging
- Centralize exception handling
- Use structured logging
- Implement retry mechanisms
- Set up monitoring
- Configure alerts

### 10. CI/CD Pipeline
- Use pre-commit hooks
- Automate testing
- Perform security scans
- Deploy infrastructure as code
- Monitor deployments 