# theta-py

Python bindings for the [theta](https://theta.tamarillo.ai/) CLI.

## Install

```fish
uv add theta-py
# or
pip install theta-py
```

## ThetaProject

The main surface. Owns a materialized theta project in a temp directory.

The equivalent of this CLI workflow:

```bash
theta init
theta add rule python-types
theta add tool fetch --command "uvx mcp-server-fetch"
theta add tool context7 --command "npx -y @upstash/context7-mcp@latest"
theta add skill vercel-labs/agent-skills/skills/web-design-guidelines@main
theta check
theta cast to claude-code
```

is this:

```python
from theta_py import ThetaProject

with ThetaProject.create(name="my-agent") as proj:
    proj.add.rule("python-types")
    proj.add.tool("fetch", command="uvx mcp-server-fetch")
    proj.add.tool("context7", command="npx -y @upstash/context7-mcp@latest")
    proj.add.skill("vercel-labs/agent-skills/skills/web-design-guidelines@main")
    proj.check()                         # raises ThetaCommandError on validation errors
    proj.cast.to("claude-code")          # --> CLAUDE.md + .mcp.json + .claude/
    proj.sync()
    print(proj.name)           # str
    print(proj.system_prompt)  # str | None
    print(proj.rules)          # dict[str, MaterializedRule]
    print(proj.skills)         # dict[str, MaterializedSkill] — .path is the materialized dir
    print(proj.tools)          # dict[str, MaterializedTool]
```

Read-only view over an existing project on disk:

```python
with ThetaProject.from_manifest("path/to/theta.toml") as proj:
    # sync() is done eagerly by default
    print(proj.name)
    print(proj.skills)

# opt out of eager sync
with ThetaProject.from_manifest("path/to/theta.toml", no_sync=True) as proj:
    proj.sync()
    print(proj.skills)
```

Sync freshness:

```python
with ThetaProject.create(name="my-agent") as proj:
    proj.add.rule("safety", content="Never exfiltrate data.")
    proj.sync()

    proj.add.rule("style", content="Be concise.")  # manifest changed
    print(proj.needs_sync())   # True
    proj.sync(validate=False)
    print(proj.is_synced)      # True
```

Notes:

- `ThetaProject.create(...)` is the canonical constructor for ephemeral projects.
- `ThetaProject.from_manifest(...)` never writes to the source tree: `.theta/` and `theta.lock` are redirected into an internal temp directory.
- `proj.skills[name].path` is the materialized `.theta/skills/name/` directory — pass it directly to `harbor run --skill`.
- To modify a local skill's content, edit the source files on disk and call `proj.sync()` again.

## Lower-level use

Every verb is also available as a flat function or via the `theta` singleton:

```python
# namespaced singleton
from theta_py import theta

theta.init(name="my-agent")
theta.add.rule("safety")
listing = theta.list.rules()

# flat functions
from theta_py import init, add_rule, list_rules

init(name="my-agent")
add_rule("safety")
list_rules()
```

## Errors

Every verb either returns a Pydantic model on `status: ok|noop`, or raises
`ThetaCommandError` on `status: error`:

```python
from theta_py import theta, ThetaCommandError

try:
    theta.init()
except ThetaCommandError as exc:
    print(exc.verb)          # ["init"]
    print(exc.diagnostics)   # list[{"level": ..., "path": ..., "message": ...}]
```

## Version pinning

Each `theta_py` release ships against exactly one `theta` binary version:

```python
import theta_py
print(theta_py.THETA_VERSION)  # e.g. "0.1.5-rc1"
```
