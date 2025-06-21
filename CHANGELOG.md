# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-06-21

### Added
- Initial release of ClickUp MCP Server
- Core task management functionality (create, read, update, delete)
- Support for custom task ID formats (e.g., `gh-123`, `bug-456`)
- Task search and filtering capabilities
- Space, folder, and list navigation
- Bulk operations for tasks
- Time tracking integration
- Task templates (bug report, feature request, code review)
- Task chain creation with automatic linking
- Team workload analytics
- Task completion metrics and velocity tracking
- Secure API key management with multiple config locations
- Easy installation via `uvx`
- Support for Claude Code and Claude Desktop
- Comprehensive documentation and examples

### Security
- API keys stored securely in user config directory
- No hardcoded credentials
- Environment variable support for CI/CD

### Developer Experience
- Full async/await implementation
- Type hints throughout
- Pre-commit hooks with ruff and mypy
- Comprehensive error handling
- Debug mode for troubleshooting