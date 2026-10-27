---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

A backend limits us to 10 concurrent requests, so we want to lower our HTTP requester connection pool to 10. Good idea?
