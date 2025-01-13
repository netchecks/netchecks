---
title: Testing
description: Netchecks testing on GitHub Actions and locally.
---

Both the Netchecks command line tool and Kubernetes operator have comprehensive test suites that run on GitHub Actions after every commit. The GitHub Actions workflows for testing can be found [here](https://github.com/hardbyte/netchecks/tree/main/.github/workflows).


## Testing the Netchecks Python Library

```bash
uv run pytest
```