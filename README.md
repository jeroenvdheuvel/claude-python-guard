# Claude Python Guard

A Claude Code PreToolUse hook that runs [Bandit](https://bandit.readthedocs.io/) static analysis on any `python -c` command before it executes. Safe commands run without interruption; commands with security findings prompt you to allow or deny before anything executes.

## Why

Claude Code can run arbitrary `python -c` commands. While Claude's auto-mode classifier catches obvious risks, it doesn't perform static analysis. This hook adds a dedicated security layer that catches real vulnerability patterns: deserialization attacks, use of `eval`/`exec`, weak cryptography, deprecated unsafe functions, and more.

## How it works

1. The hook fires on every `Bash` tool call matching `python*`
2. The full command is piped into the Docker container
3. The entrypoint extracts the `-c` argument using Python's `shlex` for correct quote handling
4. Bandit runs static analysis on the extracted code
5. **No issues found** → the hook returns `allow` and the command runs silently
6. **Issues found** → the hook returns `ask` with the Bandit finding as the reason, and Claude Code pauses to show you a prompt:

```
Bandit: >> Issue: [B307:blacklist] Use of possibly insecure function - consider using safer ast.literal_eval.

Allow this command to run?  [Allow] [Deny]
```

You decide whether to proceed. Denying prevents the command from running; allowing lets it through for that invocation only.

## Setup

### 1. Pull the Docker image

```bash
docker pull ghcr.io/jeroenvdheuvel/claude-python-guard:latest
```

To pin to a specific release, use a tag instead:

```bash
docker pull ghcr.io/jeroenvdheuvel/claude-python-guard:0.1.0
```

### 2. Configure the Claude Code hook

Add the following to your `~/.claude/settings.json` inside the `hooks.PreToolUse` array:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "docker run --rm -i ghcr.io/jeroenvdheuvel/claude-python-guard:latest --severity-level medium --confidence-level medium",
      "if": "Bash(python*)",
      "timeout": 10
    }
  ]
}
```

### Building locally (optional)

Only needed if you want to modify the hook or test changes before publishing:

```bash
docker build -t claude-python-guard .
```

## Customising severity and confidence

Pass Bandit arguments directly in the `docker run` command:

```bash
# MEDIUM severity + MEDIUM confidence (default)
docker run --rm -i ghcr.io/jeroenvdheuvel/claude-python-guard:latest --severity-level medium --confidence-level medium

# HIGH severity only (more permissive)
docker run --rm -i ghcr.io/jeroenvdheuvel/claude-python-guard:latest --severity-level high --confidence-level high

# Restrict to specific test IDs
docker run --rm -i ghcr.io/jeroenvdheuvel/claude-python-guard:latest --severity-level medium -t B301,B302,B307
```

See `docker run --rm --entrypoint bandit ghcr.io/jeroenvdheuvel/claude-python-guard:latest --list` for all available test IDs.

## What triggers a prompt (at medium/medium)

| Test ID | Pattern |
|---------|---------|
| B102 | `exec()` usage |
| B301 | `pickle.loads()` |
| B302 | `marshal.loads()` |
| B306 | `tempfile.mktemp()` |
| B307 | `eval()` |
| B324 | Weak hash functions (MD5, SHA1) |
| B506 | `yaml.load()` without safe loader |
| B104 | Binding to all interfaces (`0.0.0.0`) |

## What passes through

Safe operations like JSON parsing, loops, regex, `os.path`, `datetime`, `collections`, and standard library usage pass without interference.
