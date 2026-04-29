# Release Guide

## Versioning

Public releases use semantic version tags such as `v0.1.0`.
Internal milestone tags such as `2026.18.1` may still exist, but they do not trigger packaging or publishing.

## Release outputs

A tagged release publishes:

- Python sdist and wheel to PyPI
- macOS standalone binaries to GitHub Releases
- an updated Homebrew formula to the dedicated tap repository

## Required GitHub configuration

Repository variables:

- `HOMEBREW_TAP_REPO`: target tap repository, for example `Latentik/homebrew-agentrail`
- `HOMEBREW_TAP_FORMULA_PATH`: optional override, defaults to `Formula/agentrail.rb`

Repository secrets:

- `HOMEBREW_TAP_TOKEN`: token with write access to the tap repository

PyPI publishing:

- Prefer GitHub trusted publishing with PyPI instead of storing a long-lived API token.

## Release process

1. Update `src/agentrail/__init__.py` and `pyproject.toml` to the intended release version.
2. Merge release-ready changes to `main`.
3. Create and push a semver tag such as `v0.1.0`.
4. GitHub Actions will run CI, build Python artifacts, build macOS binaries, create or update the GitHub Release, publish to PyPI, and update the Homebrew tap.

## Rollback

If a release job fails after the GitHub Release is created, fix the issue and rerun the workflow or cut a new patch release. Avoid mutating published PyPI versions.
