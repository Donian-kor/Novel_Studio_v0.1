# Cline Python Agent Rules

## Agent Workflow

- When the user requests a change, first inspect the project structure and all relevant files.
- Use Cline tools to read, search, edit, and run commands whenever appropriate.
- Do not ask the user to locate code that can be found by inspecting the project.
- Prefer directly modifying the relevant files instead of giving manual editing instructions.
- Before editing, identify the smallest safe change.
- After editing, re-read or inspect the modified files.
- When practical, run an appropriate syntax check, test, or application command.
- Do not consider a task complete until the result has been verified as much as possible.

## Error Fixing

When an error is reported:

1. Read the complete error message and traceback.
2. Identify the file and code involved.
3. Inspect related files when necessary.
4. Determine the actual cause before changing code.
5. Fix the cause rather than hiding the symptom.
6. Check for side effects.
7. Verify the result when possible.
8. Explain the result to the user in simple Korean.

## Beginner-Friendly Behavior

- The user cannot reliably identify Python files, functions, classes, or line numbers.
- Do not tell the user to manually search through code unless absolutely necessary.
- If Cline can inspect or modify the file, do it directly.
- If the user must perform an action manually, provide exact step-by-step instructions.
- Never assume the user understands a traceback or programming terminology.

## Large or Risky Changes

- Before destructive or large-scale changes, clearly explain what will be changed and why.
- Be especially careful with file deletion, project restructuring, dependency changes, database/data changes, and major UI changes.
- Do not perform unrelated cleanup during a requested fix.

## Completion

After completing a task, report briefly:

- What was changed
- Which files were changed
- Whether the change was tested
- What the user should do next

# test