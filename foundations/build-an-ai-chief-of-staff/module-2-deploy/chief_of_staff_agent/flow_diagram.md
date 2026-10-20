# Chief of Staff Agent Architecture

```mermaid
graph TD
    User[User] --> Chief[Chief of Staff Agent]
    Chief --> Memory[CLAUDE.md]
    Chief --> FinData[financial_data/]
    Chief --> Tools
    Chief --> Commands[Slash Commands]
    Chief --> Styles[Output Styles]
    Chief --> Hooks[Hooks]

    Tools --> Agent[Agent Tool]
    Agent --> FA[Financial Analyst]
    Agent --> Recruiter[Recruiter]

    FA --> Scripts1[Python Scripts]
    Recruiter --> Scripts2[Python Scripts]

    style Chief fill:#f9f,stroke:#333,stroke-width:3px
    style Agent fill:#bbf,stroke:#333,stroke-width:2px
    style FA fill:#bfb,stroke:#333,stroke-width:2px
    style Recruiter fill:#bfb,stroke:#333,stroke-width:2px
```

## Expected Agent Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant Chief as Chief of Staff
    participant Agent as Agent Tool
    participant FA as Financial Analyst
    participant Scripts as Python Scripts
    participant Hooks as Post-Write Hook
    User->>Chief: /budget-impact hiring 5 engineers
    Chief->>Chief: Expand slash command
    Chief->>Agent: Delegate financial analysis
    Agent->>FA: Analyze hiring impact
    FA->>Scripts: Execute hiring_impact.py
    Scripts-->>FA: Return analysis results
    FA->>FA: Generate report
    FA-->>Agent: Return findings
    Agent-->>Chief: Subagent results
    Chief->>Chief: Write report to disk
    Chief->>Hooks: Trigger post-write hook
    Hooks->>Hooks: Log to audit trail
    Chief-->>User: Executive summary
```
