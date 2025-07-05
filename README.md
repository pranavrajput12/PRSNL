# AI Collaborative Development Project

This repository demonstrates a structured approach to collaborative software development using multiple AI agents.

## 🤖 AI Agents

- **Claude Code**: Primary architect and complex feature lead
- **Windsurf**: Scaffolds new modules and performs large-scale refactors. See [WINDSURF.md](WINDSURF.md).
- **Gemini CLI**: Minor edits and quick fixes. See [GEMINI.md](GEMINI.md).

## 📋 Getting Started

### For Users
1. **Start here**: [User Guide](USER_GUIDE.md) - How to work with multiple AIs
2. Understand [Git Merge Strategy](GIT_MERGE_STRATEGY.md) - Automated conflict prevention

### For AI Agents
1. Read the [AI Collaboration Guide](AI_COLLABORATION_GUIDE.md)
2. Review [AI Boundaries](BOUNDARIES.md) to understand agent limits
3. Check [Progress Tracker](PROGRESS_TRACKER.md) for active work
4. Check [open issues](../../issues) for available tasks
5. Review [open pull requests](../../pulls) to avoid duplicate work
6. Update Progress Tracker before starting work
7. Create a feature branch and start contributing

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
├── GIT_MERGE_STRATEGY.md
├── PROGRESS_TRACKER.md
├── SOP_CHECKLISTS.md
├── USER_GUIDE.md
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