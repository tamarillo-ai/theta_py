# theta-py

Python bindings for the [theta](https://theta.tamarillo.ai/) CLI.

## What it is

A thin wrapper around the `theta` binary. Every verb is exposed as a typed Python function. Pydantic models for arguments and outputs are codegen'd from the schemas the binary itself emits, so `theta-py` cannot drift from the binary it ships.

```python
import theta_py as theta

theta.init(name="my-agent")
theta.add.skill("vercel-labs/agent-skills/skills/web-design-guidelines@main")
report = theta.check()
assert report.ok
```

<!-- 
TODO: delete this
## How versioning works

`theta_py.__version__` always matches the bundled `theta` binary. Bumping theta triggers a CI rebuild that:

1. Regenerates pydantic models from `theta schema --output <verb>` for every verb.
2. Bundles platform-specific theta binaries into per-platform wheels.
3. Publishes to PyPI with the matching version.

 -->
## On versioning

The package refuses to run if a system-installed theta on `PATH` disagrees with `THETA_VERSION`.
