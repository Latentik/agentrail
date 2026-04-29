# Release Guide

## Versioning

Public releases use semantic version tags such as `v0.1.0`.
Internal milestone tags such as `2026.18.1` may still exist, but they do not trigger packaging or publishing.

## Release outputs

A tagged release publishes:

- macOS standalone binaries to GitHub Releases
- an updated Homebrew formula to the dedicated tap repository

## Required GitHub configuration

Repository variables:

- `HOMEBREW_TAP_REPO`: target tap repository, for example `Latentik/homebrew-agentrail`
- `HOMEBREW_TAP_FORMULA_PATH`: optional override, defaults to `Formula/agentrail.rb`

Repository secrets:

- `HOMEBREW_TAP_TOKEN`: token with write access to the tap repository

## Release process

1. Update `src/agentrail/__init__.py` and `pyproject.toml` to the intended release version.
2. Merge release-ready changes to `main`.
3. Create and push a semver tag such as `v0.1.0`.
4. GitHub Actions will run CI, build macOS binaries, create or update the GitHub Release, and update the `Latentik/homebrew-agentrail` tap.

## Release notes

GitHub release notes are generated automatically using `.github/release.yml`.

To keep release notes readable:

- use clear PR titles and commit subjects
- prefer Conventional Commit style subjects such as `feat:`, `fix:`, `docs:`, `ci:`, `refactor:`, `test:`, `chore:`
- apply labels that match release-note categories, especially `breaking`, `feature`, `bug`, `docs`, `ci`, `release`, `chore`, `refactor`, and `test`
- use `skip-changelog` for changes that should be excluded from release notes

## Rollback

If a release job fails after the GitHub Release is created, fix the issue and rerun the workflow or cut a new patch release.
