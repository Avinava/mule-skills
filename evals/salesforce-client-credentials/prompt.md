---
max_turns: 14
allowed_tools: [Read, Glob, Grep, Skill, WebFetch, Bash]
---

Our Mule app uses the Salesforce connector 10.x with a username and password. We want OAuth client credentials instead, with the client ID and secret stored as Runtime Manager secure properties on CloudHub 2.0. What exactly has to change, and how do we prove afterwards that it logs in the new way?
