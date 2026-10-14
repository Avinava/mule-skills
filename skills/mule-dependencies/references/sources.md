# Sources and failure modes

Read this when a lookup fails, two sources disagree, or the script needs maintenance.

## Contents

- Source order
- What each source can and cannot say
- Determinism rules
- Failure modes
- Cache and snapshot

## Source order

| Order | Source | Auth | Provides |
| --- | --- | --- | --- |
| 1 | anypoint-connect `get_exchange_asset` (agent-side, optional) | Anypoint login | Same data as the Exchange asset API, plus private assets |
| 2 | Exchange asset API (`exchange/api/v1/assets/<group>/<artifact>`) | None for public MuleSoft assets | All versions, minimum Mule version, Java support flags |
| 3 | Exchange Maven facade (`maven-metadata.xml`) | None for metadata | Version list only |
| 4 | MuleSoft releases repository (`maven-metadata.xml`) | None | Version list only; the only source for MUnit and the Mule Maven plugin |
| Runtime | Java support table in the public MuleSoft docs source repository | None | Java versions per runtime and channel |

The Exchange endpoints are not a documented public contract, so the script validates the response
shape and falls through to the next source when it changes.

## What each source can and cannot say

- Only Exchange attributes report `min-mule-version` and `is-java-<n>-supported`. They can lag the
  connector jar's own descriptor by a release. For a decision with real risk, confirm against the
  connector's release notes.
- Maven metadata reports versions only. The script marks compatibility `unknown` and warns.
- Maven Central is never queried for Mule artifacts: it holds only old uploads.
- Enterprise repositories require credentials. A 401 or 403 is reported as an authentication failure.
- Support end dates are not scraped. The cadence page is HTML and changes layout; the script returns
  its URL for the user to read.

## Determinism rules

- Versions sort numerically per component, so `1.10.0` is newer than `1.9.0`.
- Any `-DEV`, `-SNAPSHOT`, `-RC`, `-M`, alpha, or beta suffix is excluded, as is any entry Exchange
  marks as a snapshot.
- The newest compatible release is the newest release whose minimum Mule version is at or below the
  target runtime and which lists the target Java level. Unknown values do not exclude a release but
  produce a warning.
- A fixed alias map supplies coordinates, because some connectors exist under more than one group and
  only one is current.

## Failure modes

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Exit 3, authentication | Enterprise-only artifact or private asset | Use anypoint-connect while logged in, or ask for repository access |
| Exit 2, unknown alias | Not in the map | Use `group:artifact` |
| Warning: Exchange unusable | Response shape changed or service down | Result comes from Maven sources; compatibility is unknown |
| Warning: stale cache | Network failed, an older cached answer was used | Report the cache time; retry later |
| Version differs from the project's internal mirror | Mirror lags or pins | Report both; the project's mirror decides what is installable |
| Runtime table parse error | Docs table layout changed | Read the Java support page directly and report that the script needs maintenance |

## Cache and snapshot

- Responses are cached under the user cache directory (`MULE_VERSIONS_CACHE_DIR` overrides it) for
  24 hours for connectors and plugins and 7 days for runtime data. `--no-cache` bypasses it. A stale
  entry is used only when the network fails, and the result says so.
- `assets/version-snapshot.json` is the only dated artifact in this skill. It is an unverified offline
  fallback regenerated with `--refresh-snapshot`. It records the latest release per alias, the runtime
  Java table, and the generation date. Never describe a snapshot answer as current.
