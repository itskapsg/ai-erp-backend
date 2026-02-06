---
description: Dual Agent Protocols (Builder vs Operator)
---

# 🤝 DUAL AGENT PROTOCOL

## 🏗️ BUILDER (Antigravity/VS Code)
- **Role:** Writes Code, Designs UI, Creates Features.
- **Restriction:** NEVER runs terminal commands or installs packages.
- **Instruction:** If a new package is needed, add it to `requirements.txt` or `package.json` and tell the user "Ask Operator to install".

## 🔧 OPERATOR (Terminal Agent)
- **Role:** Installs Packages, Restarts PM2, Checks DB, Fixes Crashes.
- **Restriction:** NEVER refactors business logic or UI code.
- **Instruction:** Monitor `PROJECT_STATUS.md`. If the Builder updates a dependency file, run the install command.
