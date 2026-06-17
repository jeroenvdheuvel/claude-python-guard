# claude-bandit

A Claude Code PreToolUse hook that runs [Bandit](https://bandit.readthedocs.io/) static analysis on any `python -c` command before it executes, blocking dangerous inline Python code automatically.

## Why

Claude Code can run arbitrary `python -c` commands. While Claude's auto-mode classifier catches obvious risks, it doesn't perform static analysis. This hook adds a dedicated security layer that catches real vulnerability patterns: deserialization attacks, use of `eval`/`exec`, weak cryptography, deprecated unsafe functions, and more.

## How it works

1. The hook fires on every `Bash` tool call matching `python*`
2. The full command is piped into the Docker container
3. The entrypoint extracts the `-c` argument using Python's `shlex` for correct quote handling
4. Bandit runs static analysis on the extracted code
5. If Bandit finds issues at or above the configured severity/confidence threshold, the hook returns a `deny` decision and Claude's command is blocked

## Setup

### 1. Build the Docker image

```bash
docker build -t claude-bandit .
```

### 2. Configure the Claude Code hook

Add the following to your `~/.claude/settings.json` inside the `hooks.PreToolUse` array:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "docker run --rm -i claude-bandit --severity-level medium --confidence-level medium",
      "if": "Bash(python*)",
      "timeout": 10
    }
  ]
}
```

### 3. Add Python to the Claude allow list

Since the hook acts as the security gate, add Python commands to the `permissions.allow` list so Claude doesn't prompt for permission on every invocation:

```json
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(python3 *)"
    ]
  }
}
```

## Customising severity and confidence

Pass Bandit arguments directly in the `docker run` command:

```bash
# MEDIUM severity + MEDIUM confidence (default)
docker run --rm -i claude-bandit --severity-level medium --confidence-level medium

# HIGH severity only (more permissive)
docker run --rm -i claude-bandit --severity-level high --confidence-level high

# Restrict to specific test IDs
docker run --rm -i claude-bandit --severity-level medium -t B301,B302,B307
```

See `docker run --rm --entrypoint bandit claude-bandit --list` for all available test IDs.

## What gets blocked (at medium/medium)

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
