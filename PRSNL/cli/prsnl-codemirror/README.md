# PRSNL CodeMirror CLI

AI-powered repository intelligence for offline analysis and GitHub integration.

## Features

- 🔍 **Repository Analysis**: Comprehensive code analysis with AI insights
- 📊 **Pattern Detection**: Automatic detection of frameworks, architectures, and patterns
- 🚀 **Multi-depth Analysis**: Quick, standard, and deep analysis modes
- 🔄 **PRSNL Integration**: Sync results with your PRSNL knowledge base
- 💡 **AI Insights**: Get intelligent recommendations and code quality insights
- 📦 **Framework Detection**: Automatic detection of Svelte, React, FastAPI, and more
- 🏗️ **Architecture Analysis**: Identify MVC, microservices, and other patterns

## Installation

### From Source

```bash
cd cli/prsnl-codemirror
pip install -e .
```

### Using pip (when published)

```bash
pip install prsnl-codemirror
```

## Quick Start

### 1. Configure the CLI

```bash
# Set up PRSNL connection (optional)
prsnl-codemirror config --prsnl-url https://api.prsnl.fyi --prsnl-token YOUR_TOKEN

# Set up GitHub token for enhanced analysis (optional)
prsnl-codemirror config --github-token YOUR_GITHUB_TOKEN

# Set up OpenAI for local AI processing (optional)
prsnl-codemirror config --openai-key YOUR_OPENAI_KEY
```

### 2. Analyze a Repository

```bash
# Basic analysis
prsnl-codemirror audit /path/to/your/repo

# Deep analysis with patterns and insights
prsnl-codemirror audit /path/to/your/repo --depth deep --patterns --insights

# Analysis with automatic upload to PRSNL
prsnl-codemirror audit /path/to/your/repo --upload

# Save results to file
prsnl-codemirror audit /path/to/your/repo --output analysis.json
```

### 3. View Repository Information

```bash
# Show repository info and cached analyses
prsnl-codemirror info /path/to/your/repo

# Export as JSON
prsnl-codemirror info /path/to/your/repo --format json

# Export as Markdown
prsnl-codemirror info /path/to/your/repo --format markdown
```

## Commands

### `audit`

Analyze a repository with AI-powered insights.

```bash
prsnl-codemirror audit [OPTIONS] REPO_PATH
```

**Options:**
- `--depth [quick|standard|deep]`: Analysis depth level (default: standard)
- `--output/-o FILE`: Save results to JSON file
- `--upload`: Upload results to PRSNL after analysis
- `--patterns`: Include pattern detection in analysis
- `--insights`: Generate AI insights from analysis

**Examples:**
```bash
# Quick scan for basic information
prsnl-codemirror audit ./my-project --depth quick

# Full analysis with all features
prsnl-codemirror audit ./my-project --depth deep --patterns --insights --upload

# Save detailed analysis to file
prsnl-codemirror audit ./my-project --output detailed-analysis.json
```

### `config`

Configure CLI settings.

```bash
prsnl-codemirror config [OPTIONS]
```

**Options:**
- `--prsnl-url URL`: PRSNL backend URL
- `--prsnl-token TOKEN`: PRSNL API token
- `--github-token TOKEN`: GitHub personal access token
- `--openai-key KEY`: OpenAI API key for local processing
- `--debug`: Enable debug mode

**Examples:**
```bash
# View current configuration
prsnl-codemirror config

# Set up PRSNL integration
prsnl-codemirror config --prsnl-url https://api.prsnl.fyi --prsnl-token abc123

# Enable debug mode
prsnl-codemirror config --debug
```

### `sync`

Synchronize data with PRSNL backend.

```bash
prsnl-codemirror sync [OPTIONS]
```

**Options:**
- `--repo-id ID`: Sync specific repository
- `--download`: Download analyses from PRSNL
- `--clear-cache`: Clear local analysis cache

**Examples:**
```bash
# Download all analyses from PRSNL
prsnl-codemirror sync --download

# Clear local cache
prsnl-codemirror sync --clear-cache
```

### `info`

Show repository information and cached analyses.

```bash
prsnl-codemirror info [OPTIONS] REPO_PATH
```

**Options:**
- `--format [table|json|markdown]`: Output format (default: table)

## Analysis Depths

### Quick Analysis
- Basic file counting and language detection
- Simple pattern recognition
- Fast execution (< 30 seconds)

### Standard Analysis
- Comprehensive language analysis
- Framework and architecture detection
- Dependency analysis
- Code quality patterns
- Moderate execution time (30 seconds - 2 minutes)

### Deep Analysis
- All standard features
- AI-powered insights and recommendations
- Advanced pattern detection
- Security and performance analysis
- Longer execution time (2-10 minutes)

## Configuration

The CLI stores configuration in `~/.prsnl/codemirror/config.json`.

### Environment Variables

You can also use environment variables:

```bash
export PRSNL_URL="https://api.prsnl.fyi"
export PRSNL_TOKEN="your-token"
export GITHUB_TOKEN="your-github-token"
export OPENAI_API_KEY="your-openai-key"
```

### Cache Location

Analysis results are cached in `~/.prsnl/codemirror/cache/` for faster subsequent runs.

## Integration with PRSNL

When connected to a PRSNL instance, the CLI can:

1. **Upload Analysis Results**: Automatically sync analysis results to your knowledge base
2. **Download Remote Analyses**: Access analyses performed via the web interface
3. **Repository Mapping**: Link CLI analyses with GitHub repositories in PRSNL
4. **Insight Synchronization**: Share AI insights across web and CLI interfaces

## Supported Languages and Frameworks

### Languages
- Python, JavaScript, TypeScript
- React (JSX/TSX), Svelte, Vue.js
- HTML, CSS, SCSS, Sass
- Go, Rust, Java, C++, C
- PHP, Ruby, Swift, Kotlin, Scala
- SQL, Markdown, YAML, JSON

### Frameworks
- **Frontend**: React, Svelte, Vue.js, Next.js
- **Backend**: FastAPI, Django, Flask, Express.js
- **Mobile**: React Native, Flutter (detection)
- **Desktop**: Electron, Tauri (detection)

### Architecture Patterns
- Model-View-Controller (MVC)
- Microservices
- Component-based architecture
- Layered architecture

## Examples

### Analyze a Svelte Project

```bash
prsnl-codemirror audit ./my-svelte-app --depth standard --patterns --insights
```

Output includes:
- Svelte component analysis
- SvelteKit routing detection
- Component dependency mapping
- Performance recommendations

### Analyze a Python API

```bash
prsnl-codemirror audit ./my-api --depth deep --upload
```

Output includes:
- FastAPI/Django/Flask detection
- API endpoint analysis
- Database integration patterns
- Security recommendations

### Batch Analysis

```bash
# Analyze multiple repositories
for repo in ./projects/*/; do
    prsnl-codemirror audit "$repo" --depth quick --output "${repo%/}-analysis.json"
done
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   chmod +x ~/.local/bin/prsnl-codemirror
   ```

2. **Missing Dependencies**
   ```bash
   pip install --upgrade prsnl-codemirror
   ```

3. **PRSNL Connection Issues**
   ```bash
   # Test connection
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.prsnl.fyi/health
   ```

4. **GitHub API Rate Limits**
   - Set up a GitHub personal access token with `config --github-token`
   - This increases rate limits from 60 to 5000 requests per hour

### Debug Mode

Enable debug mode for detailed error information:

```bash
prsnl-codemirror config --debug
prsnl-codemirror audit ./my-repo --depth standard
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is part of the PRSNL ecosystem and follows the same license terms.

---

**Need Help?** 
- Check the [PRSNL Documentation](https://docs.prsnl.fyi)
- Open an issue on GitHub
- Join the PRSNL community discussions