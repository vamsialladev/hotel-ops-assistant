# Security and Data Privacy

## Data handled
- **Indexed:** hotel policy documents only (policies, menus, SOPs, staff notes).
- **Not indexed:** guest personal data, payment data, reservation records. The assistant answers policy questions; it does not look up guests.

## How data flows
- Documents are indexed locally. Only the top 5 matching passages and the staff member's question are sent to the Claude API for each answer.
- The API key is read from `.env`, which is excluded from git (`.gitignore`) and Docker images (`.dockerignore`). A pre-commit hook blocks committed private keys.

## Known risks and mitigations
| Risk | Mitigation |
|---|---|
| Wrong policy answer given to a guest | Answers only from sources, every fact cited, fixed refusal message when not found, evaluated on every change |
| Staff see another property's rules | Property filter applied before search; covered by a unit test |
| Outdated policy used | Documents marked `status: superseded` are never indexed |
| Staff paste guest details into a question | Planned for Project 4: personal data redaction before any API call |
| Prompt injection inside a document | Documents are written by the hotel's own staff; Project 4 adds content checks for uploaded files |

## Reporting
This is a portfolio project. Report issues by opening a GitHub issue.
