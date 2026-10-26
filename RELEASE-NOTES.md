# KpihX-Labs 0.2.0

- Add Typer/Rich scan, compare and info commands with recursive --help-all,
  detailed parameter help, examples and clean input errors.
- Preserve historical file/stdin --json invocations and all core scores/signals.
- Add local analysis timings and explicit English-tokenization/marker limitations.
- Make the distinction between installed heuristics and the separate upstream
  multilingual research/training pipeline visible in the CLI itself.
- Add regression tests for help, JSON purity, compatibility, core parity and errors.
- Verify Python 3.9 separately: keep eager Annotated metadata for Typer 0.23;
  postponed annotations otherwise silently lose explicit options and arguments.

## KpihX-Labs 0.1.2

- Include the unmodified upstream MIT notice in wheel and sdist, checked by tests.
- Exclude editor backups and align bootstrap, operational docs and Python provisioning on UV.
- Add UV configuration for the retained research pipeline, with explicit hardware profiles.
- Run the lightweight nested pipeline checks from the active root CI workflow.
- Add bootstrap quoting/failure-propagation and UV-governance regression tests.

## 0.1.1

- Preserve upstream MIT attribution and full Git history.
- Publish and expose the CLI as `lynote-ai`, with internal import `aidetect`.
- Adopt uv_build and uv-only project commands.
- Add explicit two-remote push and PyPI build/publication targets.
- Preserve local heuristics; a low score does not certify human authorship.
