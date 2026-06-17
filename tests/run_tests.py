#!/usr/bin/env python3
import json
import subprocess
import sys

IMAGE = "claude-python-guard"
BANDIT_ARGS = ["--severity-level", "medium", "--confidence-level", "medium"]

TESTS = [
    # (name, python_code, expect_blocked)
    # Dangerous — should be blocked
    ("eval() usage",               "eval('1+1')",                                         True),
    ("exec() usage",               "exec('x=1')",                                         True),
    ("pickle.loads()",             "import pickle; pickle.loads(b'')",                    True),
    ("marshal.loads()",            "import marshal; marshal.loads(b'')",                  True),
    ("weak MD5 hash",              "import hashlib; hashlib.md5(b'x')",                   True),
    ("yaml.load() without loader", "import yaml; yaml.load('x: 1')",                      True),
    # Safe — should be allowed
    ("json.loads()",               "import json; json.loads('{\"a\": 1}')",               False),
    ("list comprehension",         "x = [i for i in range(10)]",                          False),
    ("os.path.join()",             "import os; os.path.join('/usr', 'local')",            False),
    ("datetime.now()",             "from datetime import datetime; datetime.now()",        False),
    ("regex match",                "import re; re.match(r'\\d+', '123')",                 False),
    ("collections.Counter()",      "from collections import Counter; Counter([1,2,3])",   False),
]

passed = 0
failed = 0

for name, code, expect_blocked in TESTS:
    payload = json.dumps({"tool_input": {"command": f"python -c \"{code}\""}})
    result = subprocess.run(
        ["docker", "run", "--rm", "-i", IMAGE, *BANDIT_ARGS],
        input=payload,
        capture_output=True,
        text=True,
    )

    try:
        output = json.loads(result.stdout)
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision", "")
    except (json.JSONDecodeError, AttributeError):
        decision = ""

    blocked = decision == "ask"
    allowed = decision == "allow"

    if blocked == expect_blocked and (blocked or allowed):
        label = "ask  " if blocked else "allow"
        print(f"PASS [{label}] {name}")
        passed += 1
    else:
        expected = "ask  " if expect_blocked else "allow"
        got = f"ask" if blocked else f"allow" if allowed else f"unknown (decision={decision!r})"
        print(f"FAIL [{expected} expected, got {got}] {name}")
        if result.stderr:
            print(f"       stderr: {result.stderr.strip()}")
        failed += 1

print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
