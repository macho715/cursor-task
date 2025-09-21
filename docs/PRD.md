# PRD (Product Requirements Doc)

<!-- Minimal, machine-parsable blocks. tm parser reads only this YAML block to generate tasks.json -->
```yml
meta:
  id: prj-hybrid-ide
  owner: "Solo Dev <dev@example.com>"
  repo: "your-repo"
  due: "2025-10-05"
  risk_tolerance: "low"   # low|med|high
  incoterms: "N/A"        # keep generic domain field

objectives:
  - "Generate tasks.json 100% from PRD; rework <5%"
  - "Safe multi-file apply under .cursor/rules guard"
  - "Use Shrimp MCP for dependency/complexity management"

deliverables:
  - "tasks.json (auto-generated)"
  - ".cursor/rules 4-pack"
  - "~/.cursor/mcp.json registration"

constraints:
  - "No secrets in Git (enforced by 20-security.md)"
  - "External calls: timeout 15s, retry 3, backoff 2x"
  - "Windows: pin Shrimp absolute path"

modules:
  - id: core-setup
    title: "Core Setup (PRD, Rules, MCP)"
    value: "high"
    acceptance:
      - ".cursor/rules present"
      - "~/.cursor/mcp.json registers shrimp"

  - id: parse-and-reflect
    title: "Parse PRD → Reflect Tasks"
    value: "high"
    acceptance:
      - "tasks.json exists"
      - "each task has deps and complexity"

  - id: agent-apply-ask
    title: "Agent Safe Apply (Ask)"
    value: "high"
    acceptance:
      - "Large changes require diff-confirm"
      - "Violations of rules abort apply"

work_items:
  - summary: "Author PRD template"
    module: core-setup
    type: doc
    est: "1h"
  - summary: "Add Rules 4-pack"
    module: core-setup
    type: code
    est: "0.5h"
  - summary: "Generate tasks.json via tm parse"
    module: parse-and-reflect
    type: cli
    est: "0.2h"
  - summary: "Reflect with Shrimp MCP (deps/complexity)"
    module: parse-and-reflect
    type: mcp
    est: "0.3h"
  - summary: "Apply with agent --apply=ask"
    module: agent-apply-ask
    type: ide
    est: "0.2h"

quality_gates:
  - "Done/Planned ≥ 85%"
  - "Rework < 5%"
  - "tasks.json lint pass"
```
