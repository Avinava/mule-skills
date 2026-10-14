---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

A Mule flow must read a multi-GB CSV file from SFTP and load the rows into a database. How should I design it so it does not run out of memory and handles bad rows and restarts?
