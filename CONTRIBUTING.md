# Contributing to Music Tools API

Thank you for your interest in contributing to the Music Tools API! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed on your system
- Redis server
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/AdarBahar/music-tools-API.git
   cd music-tools-API
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install development dependencies
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env file as needed
   ```

5. **Start Redis**
   ```bash
   redis-server
   ```

6. **Run the development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Writing Tests
- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

## 🎨 Code Style

We use several tools to maintain code quality:

### Formatting
```bash
# Format code with Black
black .

# Sort imports with isort
isort .
```

### Linting
```bash
# Check code style
flake8

# Type checking
mypy .
```

### Pre-commit Hooks
Install pre-commit hooks to automatically check code before commits:
```bash
pre-commit install
```

## 📝 Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(api): add support for playlist downloads

Add endpoint to download entire YouTube playlists
- Support for public playlists
- Configurable quality settings
- Progress tracking for batch downloads

Closes #123
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**
   - OS and version
   - Python version
   - Package versions (`pip freeze`)

2. **Steps to reproduce**
   - Clear, numbered steps
   - Expected vs actual behavior
   - Error messages and logs

3. **Additional context**
   - Screenshots if applicable
   - Sample files that cause issues
   - Configuration details

## 💡 Feature Requests

For feature requests, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and why it's valuable
3. **Provide examples** of how it would work
4. **Consider implementation** complexity and alternatives

## 🔧 Development Guidelines

### Code Organization
- Keep functions small and focused
- Use type hints for all function parameters and returns
- Add docstrings for all public functions and classes
- Follow the existing project structure

### API Design
- Follow RESTful principles
- Use appropriate HTTP status codes
- Provide clear error messages
- Include comprehensive documentation

### Performance
- Consider memory usage for large files
- Implement proper cleanup for temporary files
- Use async/await for I/O operations
- Add appropriate timeouts

### Security
- Validate all user inputs
- Sanitize file paths
- Implement rate limiting where appropriate
- Never expose internal paths or sensitive information

## 📚 Documentation

### API Documentation
- Update OpenAPI schemas when adding endpoints
- Include examples in docstrings
- Test documentation examples

### README Updates
- Keep installation instructions current
- Update feature lists for new functionality
- Include performance notes for new features

## 🚀 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test your changes**
   ```bash
   pytest
   black .
   isort .
   flake8
   mypy .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### PR Requirements
- [ ] Tests pass
- [ ] Code is formatted (Black, isort)
- [ ] No linting errors (flake8)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## 📞 Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Documentation**: Check the README and API docs first

Thank you for contributing to Music Tools API! 🎵
