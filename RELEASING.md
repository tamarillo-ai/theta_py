# Releasing

```fish
git tag v0.0.X-rc1; git push origin v0.0.X-rc1   # --> TestPyPI
git tag v0.0.X;     git push origin v0.0.X       # --> TestPyPI + PyPI
```

Anything matching `-(rc|a|b|alpha|beta)` stops at TestPyPI.

PyPI auth is OIDC (Trusted Publishers). No secrets in the repo. Setup is
already done on pypi.org and test.pypi.org for `theta-py` against
`tamarillo-ai/theta_py` workflow `release.yml`, environments `pypi` and
`testpypi`.

## Local dry-run

```fish
./scratch/theta-py-release-dry-run.fish 0.1.3-rc1
```

## Install a pre-release

```fish
uv pip install --index-url https://test.pypi.org/simple/ --pre theta-py
```
