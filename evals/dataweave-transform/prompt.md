---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

Write a DataWeave 2 script that takes a large JSON array of orders (each with a nested lines array) and returns one record per customer with the total amount, skipping null amounts. The input can be hundreds of MB.
