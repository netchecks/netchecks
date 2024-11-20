---
title: Release
description: How to release a new version of Netchecks
---

## Releasing Netchecks

Netchecks is released via GitHub Actions. To make a release

- Update `version` in both `pyproject.toml` and `operator/pyproject.toml`. Ensure both versions match.
- Update `version` in `operator/charts/netchecks/Chart.yaml`
- Update `appVersion` in `operator/charts/netchecks/Chart.yaml`. Ensure this matches the `version` in the aforementioned `pyproject.toml` files.
- Update `version` in `operator/charts/netchecks/Chart.yaml`.
- Make PR against the `main` branch and merge.
- Create a GitHub release with the tag `v<semver>`, where `semver` is the same version as set in the `pyproject.toml` files.
- Note that a Helm release will automatically be created.

Note that the version needs to follow [semantic versioning](https://semver.org/).
