#!/usr/bin/env python3
import sys, shlex, os, tempfile, subprocess, json

data = json.load(sys.stdin)
command = data.get('tool_input', {}).get('command', '')

if not command:
    sys.exit(0)

try:
    args = shlex.split(command)
except ValueError:
    sys.exit(0)

code = None
for i, arg in enumerate(args):
    if arg == '-c' and i + 1 < len(args):
        code = args[i + 1]
        break

if not code:
    sys.exit(0)

with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
    f.write(code)
    tmpfile = f.name

try:
    result = subprocess.run(['bandit', *sys.argv[1:], '-q', tmpfile], capture_output=True, text=True)
    decision = {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow'}
    if result.returncode != 0:
        issue = next((line for line in result.stdout.splitlines() if 'Issue:' in line), 'Security issue detected')
        decision['permissionDecision'] = 'ask'
        decision['permissionDecisionReason'] = f'Bandit: {issue}'
    print(json.dumps({'hookSpecificOutput': decision}))
finally:
    os.unlink(tmpfile)
