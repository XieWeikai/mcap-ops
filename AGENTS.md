# Repository workflow

- Author in the local checkout. Run all builds and tests on SSH host `reference-linux`,
  in `.`, using project-local tooling.
- Keep `mcap-ops-core` independent of files, Python, robot schemas and datasets.
- Preserve original timestamps and source data. Detection, selection and
  transformation are separate interfaces.
- Document units, clock/causality, gap handling, shape, errors and provenance.
- Test behavior through public interfaces with generated fixtures; never use or
  modify an unrelated recording or running robotics service.
- Git commits must be coherent and local/remote histories must agree. Never
  overwrite divergent remote commits or unexpected worktree changes.
- Third-party Xpark files are reference material only, not part of this package.
