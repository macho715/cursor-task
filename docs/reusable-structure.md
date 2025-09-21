# Reusable Project Structure

This repository packages the hybrid AI development workflow so that it can be bootstrapped into any project in a repeatable way. The reusable pieces live under `tools/` and are copied into new projects with the `setup_new_project.py` scaffold script.

## Key Building Blocks

- **tools/reflection/** - reusable Python package that loads tasks, scores complexity, and renders reports. The `TaskReflector` class is imported by CLIs or other automation.
- **tools/tasks_reflect.py** - command-line interface that runs reflection in any repository. Accepts optional config overrides so that downstream projects can tune weights.
- **tools/execute_priority.py** and **tools/parallel_executor.py** - execution helpers that reuse reflection output to run priority or parallel workflows.
- **tools/setup_new_project.py** - scaffold generator that produces a fresh project structure, copies all required tools, and wires example configs.
- **.github/workflows/reflect.yml** - ready-to-use CI pipeline that can be dropped into new repositories without edits.

## Generated Layout

Running `python tools/setup_new_project.py --project-name my-workflow` will produce the following folder structure:

```
my-workflow/
  docs/
    PRD.md                     # requirements template seeded with reusable modules
  reports/
    tasks_reflect_report.md    # created after the first reflection run
  tools/
    tasks_reflect.py
    execute_priority.py
    parallel_executor.py
    dag_visualizer.py
    auto_reflector.py
    reflection/               # shared library package
      __init__.py
      config.py
      core.py
      exceptions.py
    setup_git_hooks.py
    conventional_commits.py
    watchdog_config.yaml       # profile-specific copy
    priority_config.yaml       # team-size specific copy
  .github/workflows/
    reflect.yml
  .cursor/rules/
  src/
  tests/
  tasks.json                   # starter task graph
  LICENSE
  .gitignore
```

This layout is intentionally opinionated: all reusable automation stays inside `tools/` (and its `reflection` package) so downstream projects only import from one place.

## Workflow for New Projects

1. **Generate the scaffold**
   ```bash
   python tools/setup_new_project.py \
     --project-name my-workflow \
     --type web \
     --team-size startup
   ```
   Add `--destination` to place the scaffold elsewhere or `--force` to reuse an existing directory.

2. **Review configuration**
   - Adjust `docs/PRD.md` to match the new project.
   - Optionally create a custom reflection config and pass it via `--config` to `tools/tasks_reflect.py`.

3. **Run the core automation**
   ```bash
   python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md
   python tools/dag_visualizer.py --input tasks.reflected.json
   python tools/execute_priority.py --input tasks.reflected.json --strategy dependency
   ```

4. **Wire CI and git hooks**
   - Run `python tools/setup_git_hooks.py --install` inside the new project.
   - Commit the generated `.github/workflows/reflect.yml` to enable automated reflection on each push.

5. **Extend as needed**
   - Import `from tools.reflection import TaskReflector` in application code to embed reflection logic.
   - Store team-specific weights in YAML/JSON configs and load them with `load_config`.

## Design Principles

- **Single source of truth** - the `reflection` package encapsulates all algorithms so that CLIs and scripts stay thin wrappers.
- **Copy, then customise** - scaffolding duplicates the toolkit into the target project so teams can iterate independently without cross-repo coupling.
- **Configurable** - weightings, thresholds, and watcher patterns are file-based; new projects can override them without editing the library.
- **Automation first** - every copied script is executable both locally and in CI to keep behaviour consistent across environments.

With this structure in place, the same workflow can be reproduced in any repository by running one command and tailoring the generated artefacts.
