# Contributing to Neo Execution Specs

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of Neo N3 protocol

### Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/neo-execution-specs.git
cd neo-execution-specs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[all]"

# Verify setup
pytest
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes

- Write code following the style guide
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=neo

# Run type checking
mypy src/neo
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring

### 5. Submit PR

Push your branch and create a pull request on GitHub.

## Code Style

### Python Style

- Follow PEP 8
- Use type hints for all public APIs
- Maximum line length: 100 characters
- Use `ruff` for linting

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `ExecutionEngine` |
| Functions | snake_case | `get_balance` |
| Constants | UPPER_SNAKE | `MAX_STACK_SIZE` |
| Private | _prefix | `_internal_method` |

### Documentation

- All public functions need docstrings
- Use Google-style docstrings

```python
def execute_script(script: bytes, gas_limit: int = 0) -> ExecutionResult:
    """Execute a Neo VM script.
    
    Args:
        script: The script bytes to execute.
        gas_limit: Maximum gas to consume (0 = unlimited).
    
    Returns:
        ExecutionResult containing state and stack.
    
    Raises:
        VMException: If execution fails.
    """
```

## Pull Request Guidelines

### Requirements

- [ ] All tests pass
- [ ] Code follows style guide
- [ ] New code has tests
- [ ] Documentation updated
- [ ] Commit messages are clear

### PR Title Format

```
type(scope): description

Examples:
feat(vm): add CALLT instruction support
fix(crypto): correct Ed25519 signature verification
docs: update API documentation
```

### Review Process

1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Address feedback if needed
4. Merge when approved

## Testing Guidelines

### Writing Tests

- Test one thing per test function
- Use descriptive test names
- Include edge cases
- Add test vectors for cross-validation

```python
def test_add_positive_integers():
    """ADD instruction with positive integers."""
    engine = ExecutionEngine()
    sb = ScriptBuilder()
    sb.emit_push(3)
    sb.emit_push(5)
    sb.emit(OpCode.ADD)
    
    engine.load_script(sb.to_array())
    engine.execute()
    
    assert engine.result_stack.peek().get_integer() == 8
```

## Questions?

- Open an issue for questions
- Join Neo Discord for discussions
- Check existing issues before creating new ones
