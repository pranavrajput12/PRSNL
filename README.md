# AI Collaborative Development Project

This repository demonstrates a structured approach to collaborative software development using multiple AI agents.

## 🤖 AI Agents

- **Claude Code**: Primary architect and complex feature lead
- **Windsurf**: Scaffolds new modules and performs large-scale refactors. See [WINDSURF.md](WINDSURF.md).
- **Gemini CLI**: Minor edits and quick fixes. See [GEMINI.md](GEMINI.md).

## 📋 Getting Started

1. Read the [AI Collaboration Guide](AI_COLLABORATION_GUIDE.md)
2. Review [AI Boundaries](BOUNDARIES.md) to understand agent limits
3. Check [open issues](../../issues) for available tasks
4. Review [open pull requests](../../pulls) to avoid duplicate work
5. Create a feature branch and start contributing

## 🛠 Development Workflow

```bash
# Sync with latest changes
git pull --rebase

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push and create PR
git push -u origin feature/your-feature-name
```

## 📁 Project Structure

```
.
├── .github/              # GitHub templates and workflows
├── docs/                 # Project documentation
├── src/                  # Source code (when added)
├── tests/                # Test files (when added)
├── AI_COLLABORATION_GUIDE.md
├── BOUNDARIES.md
├── CLAUDE.md
├── GEMINI.md
├── WINDSURF.md
└── README.md
```

## 🔧 Configuration

- Git hooks: [To be configured]
- CI/CD: [To be configured]
- Testing: [To be configured]

## 📝 Contributing

All contributions must follow the guidelines in [AI_COLLABORATION_GUIDE.md](AI_COLLABORATION_GUIDE.md).

## 📄 License

[To be determined]

---

*Generated and maintained by AI agents following strict collaboration protocols.*