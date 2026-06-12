# install cargo dev tools via cargo-binstall
[group: 'codegen']
codegen:
    uv run python -m theta_py._codegen --binary $(which theta) --theta-version $(theta --version | awk '{print $2}')

# run pytests
[group: 'test']
test:
    THETA_BIN=$(which theta) uv run pytest .

test-nn:
    THETA_BIN=$(which theta) uv run pytest -q -m "not network"

# launch ipython with THETA_BIN pointed at the system theta
[group: 'dev']
repl:
    THETA_BIN=$(which theta) uv run ipython