
# .cursor/rules/rapid-development.rules

# 1. Project Conventions
- This project uses Python 3.9+ for Lambda functions, AWS SAM for local development and deployment, and API Gateway with no authentication. The services are structured as microservices (math and weather) running as Lambda functions.
- All component files must be named in PascalCase (e.g., MyComponent.tsx).
- Use the lodash library for utility functions.

# 2. Root Cause Fixes
- Important: Always address the root cause of issues, not just the symptoms.
- Do not apply temporary workarounds or shortcuts.

# 3. Minimal and Relevant Context
- Only modify files explicitly referenced in the prompt or context.
- Do not make changes to unrelated files.

# 4. Small, Readable, Testable Classes/Services
- Service and utility classes must be concise and focused, ideally fitting within a single screen.
- Use dependency injection (DI) or inversion of control (IoC) patterns where appropriate.
- Avoid large, monolithic classes.

# 5. Direct, Actionable Output
- Do not provide high-level summaries unless requested.
- When asked for a fix or explanation, provide actual code or a direct answer first, then explanations if needed.
