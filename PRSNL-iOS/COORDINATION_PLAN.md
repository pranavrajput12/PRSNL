# PRSNL iOS Development Coordination Plan

## Claude02 ↔️ Kilo Code Collaboration

### 🤝 Roles & Responsibilities

#### Kilo Code (Lead Orchestrator)
- **Primary**: Implementation, coding, testing
- **Owns**: All code generation and Xcode project management
- **Decides**: UI/UX implementation details, Swift patterns
- **Reports**: Progress updates, blockers, questions

#### Claude02 (Technical Advisor)
- **Primary**: Architecture guidance, code review, documentation
- **Owns**: API contract maintenance, integration guidance
- **Decides**: Architecture patterns, security approaches
- **Reports**: Backend changes, best practices

### 📋 Documentation Exchange

#### From Kilo Code → Claude02
After initial review, I need:

1. **`IMPLEMENTATION_STATUS.md`**
   ```markdown
   # iOS Implementation Status
   
   ## Completed Features
   - [ ] Project setup
   - [ ] API client
   - [ ] Timeline view
   - [ ] Search functionality
   - [ ] Item detail view
   - [ ] Capture screen
   - [ ] Settings
   - [ ] Share extension
   
   ## Current Blockers
   - Issue: [Description]
   - Attempted: [What was tried]
   - Need: [What kind of help needed]
   
   ## Architecture Decisions Made
   - [Decision]: [Reasoning]
   
   ## Questions for Claude02
   1. [Specific technical question]
   ```

2. **`API_INTEGRATION_LOG.md`**
   ```markdown
   # API Integration Log
   
   ## Working Endpoints
   - ✅ GET /timeline
   - ✅ POST /capture
   
   ## Issues Found
   - Endpoint: [path]
   - Expected: [behavior]
   - Actual: [what happened]
   - Workaround: [if any]
   ```

3. **`SWIFT_PATTERNS.md`**
   - Custom patterns developed
   - Reusable components created
   - Performance optimizations

#### From Claude02 → Kilo Code
I'll provide:

1. **Backend Updates** (when relevant)
2. **Security Recommendations**
3. **Performance Guidelines**
4. **Code Review Feedback**

### 🔄 Communication Protocol

#### 1. Progress Updates
```markdown
## Daily Update Format
Date: YYYY-MM-DD
Completed:
- [Feature/task completed]
In Progress:
- [Current work]
Blocked:
- [Any blockers]
Next:
- [What's planned next]
```

#### 2. Technical Questions
```markdown
## Question Template
Context: [What you're trying to achieve]
Problem: [Specific issue]
Tried: [What solutions attempted]
Code:
```swift
// Relevant code snippet
```
Question: [Specific question]
```

#### 3. API Issues
```markdown
## API Issue Report
Endpoint: [Full path]
Method: [GET/POST/etc]
Headers: [What was sent]
Body: [Request body if applicable]
Expected: [What should happen]
Actual: [What happened]
Response: [Full response]
```

### 🎯 Task Management

#### Phase-Based Checkpoints

**Phase 1: Foundation ✅**
- Kilo: "Foundation complete, API client works"
- Claude02: Reviews implementation, provides feedback

**Phase 2: Core Features**
- Kilo: "Timeline and search working, need help with [specific issue]"
- Claude02: Assists with architecture/API questions

**Phase 3: Advanced Features**
- Kilo: "Share extension started, WebSocket questions"
- Claude02: Provides WebSocket guidance

**Phase 4: Polish**
- Kilo: "Ready for review, performance concerns about [feature]"
- Claude02: Final review and optimization suggestions

### 🚨 Escalation Path

#### When to Ask Claude02
1. **Architecture Changes**: Before making major structural changes
2. **API Confusion**: When endpoint behavior doesn't match documentation
3. **Security Concerns**: Any authentication/data protection questions
4. **Performance Issues**: When optimization is needed
5. **Backend Bugs**: If you suspect backend issues (don't fix, just report)

#### Quick Questions vs Deep Dives
- **Quick**: "Is this the right API endpoint for X?"
- **Deep**: "Should we restructure the entire networking layer because..."

### 📁 File Organization

```
PRSNL-iOS/
├── Documentation/           # Original docs from Claude02
│   ├── *.md
├── Implementation/          # Kilo's work
│   ├── PRSNL.xcodeproj
│   ├── PRSNL/
│   └── PRSNLTests/
├── Coordination/           # Ongoing communication
│   ├── IMPLEMENTATION_STATUS.md
│   ├── API_INTEGRATION_LOG.md
│   ├── DAILY_UPDATES.md
│   └── QUESTIONS_AND_ANSWERS.md
```

### 🔍 Code Review Process

1. **Kilo Implements Feature**
2. **Updates IMPLEMENTATION_STATUS.md**
3. **Requests Review** (if needed)
4. **Claude02 Reviews**:
   - Architecture adherence
   - API usage correctness
   - Security best practices
   - Performance considerations
5. **Feedback Provided**
6. **Kilo Iterates**

### 💡 Best Practices

#### For Kilo Code
1. **Document Decisions**: Record why you chose specific approaches
2. **Test with Real Backend**: Always verify against running backend
3. **Ask Early**: Don't wait until you're deep into implementation
4. **Show Code**: Include relevant code snippets in questions

#### For Claude02
1. **Be Available**: Respond to blockers quickly
2. **Provide Examples**: Show, don't just tell
3. **Explain Why**: Help Kilo understand the reasoning
4. **Stay Updated**: Monitor for backend changes that affect iOS

### 🚀 Success Metrics

We'll know we're coordinating well when:
1. ✅ No duplicate work
2. ✅ Quick resolution of blockers
3. ✅ Clean API integration
4. ✅ Consistent architecture
5. ✅ Efficient communication

### 🆘 Emergency Contacts

If Kilo needs immediate help:
1. **API Down**: Check if backend is running
2. **Auth Failed**: Verify API key is correct
3. **Weird Behavior**: Document exactly what happened
4. **Crashes**: Share crash logs and steps to reproduce

### 📅 Suggested Workflow

1. **Kilo starts each day**: Reviews tasks, updates status
2. **Works on implementation**: Documents issues as they arise
3. **End of day**: Updates IMPLEMENTATION_STATUS.md
4. **Claude02 reviews**: Provides feedback/answers
5. **Next day**: Kilo addresses feedback, continues

This coordination plan ensures smooth collaboration while maintaining clear boundaries and efficient communication.