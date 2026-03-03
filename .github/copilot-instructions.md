# Copilot Instructions - Engineering Standards

These instructions define the mandatory quality standard for all code, tests, refactors, and documentation in this repository.

## 1) Language Policy

- **All code, comments, docs, commit messages, filenames, generated files, and written artifacts must be in English.**
- **Assistant replies to the user must always be in Portuguese.**
- Avoid mixing languages in project files unless explicitly required by an external interface.

## 2) Engineering Principles

- Prioritize simplicity, readability, and maintainability.
- Avoid overengineering and premature abstractions.
- Fix root causes instead of patching symptoms.
- Preserve public API compatibility unless requirements explicitly change.
- Keep every change small, focused, and purpose-driven.

## 3) SOLID and Design

- **S**ingle Responsibility: each module/class/function should have one clear responsibility.
- **O**pen/Closed: prefer extension through composition over risky modifications to stable code.
- **L**iskov Substitution: derived types must honor base type contracts.
- **I**nterface Segregation: keep interfaces small and specific.
- **D**ependency Inversion: depend on abstractions rather than concrete implementations when appropriate.

## 4) Typing and Function Signatures

- Require type hints for public and private functions.
- Avoid `Any` unless there is a clear technical justification.
- Prefer explicit types (`dict[str, str]`, `list[Path]`, etc.).
- Ensure all return types are annotated.
- Use `Protocol`/`TypedDict` where they improve contract clarity.

## 5) Docstrings (Google Style)

- Every public function/class must include a **Google Style** docstring.
- Include sections when applicable: `Args`, `Returns`, `Raises`, `Examples`.
- Docstrings must explain intent and contract, not restate implementation details.

Example:

```python
def calculate_total(items: list[float], tax: float) -> float:
    """Calculate total amount including tax.

    Args:
        items: List of base amounts.
        tax: Tax percentage in the range [0, 1].

    Returns:
        Total amount with tax applied.

    Raises:
        ValueError: If `tax` is outside the range [0, 1].
    """
```

## 6) Logging

- Use `logging` (not `print`) in application/library code.
- Logs must be descriptive, contextual, and actionable.
- Expected levels:
  - `DEBUG`: technical details for diagnostics
  - `INFO`: relevant normal flow events
  - `WARNING`: recoverable unexpected behavior
  - `ERROR`: operation failures
  - `CRITICAL`: severe failures blocking continuity
- Include useful context (ids, paths, operation, result).
- Never log secrets (tokens, passwords, keys).

## 7) Testing and Coverage

- Every functional change must include tests.
- Add unit tests for business rules.
- Add integration tests for cross-module/IO flows where real integration exists.
- Minimum required coverage: **80%**.
- New changes must not reduce global coverage below 80%.
- Tests must be deterministic, isolated, and fast.
- Avoid real network dependencies; use mocks/fakes when needed.

## 8) Code Quality (Lint/Format)

Before finalizing any delivery, run and pass:

1. `isort`
2. `black`
3. `ruff`
4. `flake8`
5. `pytest` with coverage >= 80%

Example local run:

```bash
isort .
black .
ruff check .
flake8 .
pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

## 9) Git and Versioning Best Practices

- Keep commits small and atomic with clear messages.
- Prefer Conventional Commits:
  - `feat: ...`
  - `fix: ...`
  - `refactor: ...`
  - `test: ...`
  - `docs: ...`
  - `chore: ...`
- Never mix unrelated changes in the same commit.
- Do not commit temp files, caches, or secrets.
- Keep `git diff` clean and scoped.

## 10) Project Structure and Organization

- Follow the current project structure.
- Do not rename/move files without clear need.
- Avoid logic duplication; extract utilities when justified.
- Update documentation when public behavior changes.

## 11) Delivery Rule

Every delivery must include:

- Typed and documented code (Google Style)
- Relevant logging
- Unit and integration tests
- Coverage >= 80%
- Passing format/lint checks (`isort`, `black`, `ruff`, `flake8`)
- Focused changes aligned with scope

If any requirement cannot be met due to technical constraints, explain it clearly in the PR and provide a remediation plan.
