# theta-py

Python bindings for the [theta](https://theta.tamarillo.ai/) CLI.

A thin wrapper around the `theta` binary. Every verb is exposed as a typed
Python function. Pydantic models for arguments and outputs are codegenerated
from the schemas the binary itself emits, so `theta-py` cannot drift from
the binary it ships.

## Install

```fish
uv add theta-py
# or
pip install theta-py
```

The matching `theta` binary is bundled inside the wheel and lands at
`<venv>/bin/theta` when the package is installed (unless your platform is not supported and the binary will be built locally as per theta installer)

## Use

Two equivalent surfaces.

```python
# namespaced, one singleton, dotted access
from theta_py import theta

theta.init(name="my-agent")
theta.add.rule("safety")
listing = theta.list.rules()
print(listing.kind)
```

```python
# flat, every verb is a top-level function
from theta_py import init, add_rule, list_rules

init(name="my-agent")
add_rule("safety")
listing = list_rules()
```

Pydantic outcome types are importable for type-hint use:

```python
from theta_py import theta
from theta_py._generated.outcomes import InitOutcome, CheckOutcome

out: InitOutcome = theta.init(name="my-agent")
report: CheckOutcome = theta.check()
assert report.valid
```

## Errors

Every verb either returns a pydantic model on `status: ok|noop`, or raises
`ThetaCommandError` on `status: error`:

```python
from theta_py import theta, ThetaCommandError

try:
    theta.init()
except ThetaCommandError as exc:
    print(exc.verb)          # ["init"]
    print(exc.diagnostics)   # list of {"level": ..., "path": ..., "message": ...}
```

Catch `ThetaInvocationError` to handle any failure (transport + envelope).

## Version pinning

`theta_py.THETA_VERSION` is the version of the `theta` binary bundled inside
the wheel. Each `theta_py` release ships against exactly one `theta` release.

```python
import theta_py
print(theta_py.THETA_VERSION)  # e.g. "0.1.3-rc1"
```

## Releases

See [`RELEASING.md`](./RELEASING.md).
