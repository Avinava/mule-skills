# Anypoint design workflow

Anypoint access is optional for local design. Use it only for requested Design Center, Exchange, or
centralized Governance work.

Read `<skills-root>/mule-ops/references/anypoint-readiness.md`, then use the **Design capability** probe:

1. `whoami` confirms authentication and organization context.
2. `list_design_center_projects` confirms Design Center visibility.
3. Use `search_exchange` only when Exchange discovery is needed.
4. Use `explain_api_governance_plan` only when centralized governance is in scope.

Do not require `list_environments`; runtime visibility is unrelated to Design Center. Never echo identity,
organization, profile, project IDs, or tenant data.

## Read, create, and synchronize

- Resolve projects by exact name or ID. List branches/files, then read the main file, `exchange.json`, and
  referenced local files.
- Create with `preview_design_center_project_create`, show the neutral action, then consume the token with
  `create_design_center_project` only after approval. RAML creation is documented; OAS creation must be
  proven in the current environment or performed through the UI with the connector gap recorded.
- Validate locally before `preview_design_center_sync`. Review create/update/unchanged actions and hashes,
  then call `sync_design_center_files` after approval. Generate a new preview after any change.
- Never write `exchange_modules`. The sync workflow does not delete, move, or rename.

## Publication

Publication is separate. Validate locally, query governance when requested, then call
`preview_exchange_publication` with exact group, asset, versions, classifier, branch, main, and name. Show
the bound source hash. Publish only after approval using `publish_previewed_exchange_asset`, and require
successful Exchange artifact hash verification.

Do not use legacy `publish_to_exchange` in new automation. Do not publish custom rulesets or create
governance profiles unless separately requested. Project, branch, file, asset, and ruleset deletion always
requires separate exact approval and is outside this skill's default workflow.

Sources: [Design Center Experience API](https://anypoint.mulesoft.com/exchange/portals/anypoint-platform/f1e97bc6-315a-4490-82a7-23abe036327a.anypoint-platform/api-designer-experience-api/minor/1.1/pages/Usage%20Examples/),
[API Designer](https://docs.mulesoft.com/design-center/design-create-publish-api-specs), and
[API Governance](https://docs.mulesoft.com/api-governance/).
