# GitHub Copilot Instructions

## Response Style

- Always respond to the user in Korean.
- Explain technical concepts in simple Korean because the user is a Python beginner.
- Do not assume that the user understands programming terminology.
- Keep Python syntax, technical terms, file names, class names, function names, variable names, and error messages in their original form when appropriate.

## Code Explanations

When explaining a change, use this structure when appropriate:

### Problem
Explain what the problem is in simple Korean.

### Cause
Explain why it happened in simple Korean.

### Changes
Explain what was changed.

### Next Step
Clearly explain what the user should do next.

Do not overwhelm the user with unnecessary code explanations.

## Code Generation

- When generating code, prefer complete, directly usable code when the user needs to copy and paste it.
- Keep code comments in Korean unless English is required by the project.
- Follow the existing project architecture and coding style.
- Do not unnecessarily rewrite working code.

## Python Environment

- Respect the Python version already used by the project.
- Respect the project's existing dependencies and configuration.
- Do not recommend installing additional packages unless they are actually needed.

## PySide6 Projects

- Use PySide6 syntax consistently when the project uses PySide6.
- Do not mix PyQt5 or PyQt6 syntax into PySide6 code.
- Preserve the separation between UI and application logic.
- Preserve Qt Designer compatibility when the project uses Qt Designer.
- Do not modify UI design or QSS unless requested.
- Use appropriate Qt threading patterns for long-running operations so the UI remains responsive.