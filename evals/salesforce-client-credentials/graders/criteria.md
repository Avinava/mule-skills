---
type: llm
weight: 1
---

Pass only if the answer says the connector must move to a version that has the OAuth Client Credentials connection type (sourced from release notes or a live lookup, not memory) and checks that version's runtime and Java needs; uses the org's My Domain token URL rather than the generic login host; references the Runtime Manager secure properties as plain ${key} and not ${secure::key}; notes the run-as user is set on the client app and can change without code; and verifies afterwards from the login record and a token identity call. Fail if it recommends ${secure::} for platform secure properties.
