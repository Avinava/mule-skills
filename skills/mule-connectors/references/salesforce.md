---
connector: salesforce
connector-version: 12.0
verified: 2026-10-26
---

# Salesforce connector profile

## Contents

- [How to use this profile](#how-to-use-this-profile)
- [Connection types by version](#connection-types-by-version)
- [Token and endpoint rules](#token-and-endpoint-rules)
- [Run-as identity](#run-as-identity)
- [Account and licence limits](#account-and-licence-limits)
- [Sources](#sources)
- [Known signatures](#known-signatures)
- [Sensitive loggers](#sensitive-loggers)
- [Identity verification](#identity-verification)
- [Non-blocking warnings](#non-blocking-warnings)
- [Changing the integration user](#changing-the-integration-user)

## How to use this profile

Rows use `Claim | Versions | Evidence | Re-verify by`. Release-notes rows re-verify with
`mule_versions.py notes salesforce --grep "<term>"`. The live page covered 11.2.2 onward on the
verified date, so claims about older releases cite an archived copy of the same page
([web archive](https://web.archive.org/web/2025/https://docs.mulesoft.com/release-notes/connector/salesforce-connector-release-notes-mule-4))
and stay valid until MuleSoft changes those releases. Connector reference rows re-verify against
[the connector reference](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-reference)
or its versioned page for the project's major.

## Connection types by version

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| Connection types: Basic Authentication, OAuth 2.0, OAuth JWT, OAuth SAML, OAuth Client Credentials | 12.x | Documented: [connector reference](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-reference#sfdc-config_oauth-client-credentials) | Reference page for the installed major |
| OAuth Client Credentials was added in 11.0.0 and does not exist in 10.x; 10.x configuration errors about the unknown connection element do not say a newer major is needed | Added 11.0.0 (March 27, 2025) | Documented: 11.0.0 release notes (archived copy above); Observed: a 10.x project failed until the connector moved to 11.x | Archived release notes; `notes salesforce --grep "client credentials"` for current releases |
| 11.0.0 also removed the Subscribe Channel and Subscribe Topic listeners in favor of the Replay listeners with `ONLY_NEW`; flows using them must be rewritten during a 10.x upgrade | 11.0.0 and later | Documented: 11.0.0 release notes (archived copy above) | Archived release notes |
| OAuth Username Password connection type removed; apps that use it fail to deploy | 12.0.0 and later | Documented: [12.0.0 release notes](https://docs.mulesoft.com/release-notes/connector/salesforce-connector-release-notes-mule-4#12-0-0) | `notes salesforce --grep "username password"` |
| 11.0.0 to 11.4.0 need Mule 4.6.6 or later with Java 8, 11 or 17; 12.0.0 needs Mule 4.9.0 or later with Java 17 only; later 12.0.x patches state their own minimums (for example 4.6.22 or 4.9.9 for 12.0.1) | 11.x, 12.x | Documented: [release notes](https://docs.mulesoft.com/release-notes/connector/salesforce-connector-release-notes-mule-4) compatibility tables. The 11.5.0 table says Mule 4.4.0, which looks like a documentation error; trust the Exchange minimum | `mule_versions.py connector salesforce --mule <x> --java <n>` |
| Basic Authentication works only up to Salesforce API v64.0 | Current reference | Documented: [connector reference](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-reference#sfdc-config_basic) | Reference page heading for Basic Authentication |
| Client credentials sessions renew on `INVALID_SESSION_ID` in more operations with each release (Apex REST, Bulk v2 jobs, Apex SOAP, metadata and Partner API) | 11.2.2 to 12.0.5 | Documented: release-notes fixed issues | `notes salesforce --grep "INVALID_SESSION_ID"`; prefer the newest compatible patch |

## Token and endpoint rules

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| The client credentials Token URL is the org's My Domain token endpoint, `https://<my-domain>.my.salesforce.com/services/oauth2/token`; the generic login hosts reject this grant | All with client credentials | Documented: connector reference default value; [Salesforce client credentials flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5): requests to the generic login and test hosts are not supported, use the My Domain URL | Both pages |
| Keep the client ID and secret in one secret supply model: on CloudHub 2.0 as protected properties referenced with plain `${key}`, or encrypted in a file with `${secure::key}`. Referencing a Runtime Manager property as `${secure::key}` failed a deployment | All | Observed; see [secret supply models](../../mule-development/references/secrets-and-tls.md#secret-supply-models) | The supply-model check in `mule-build` 3.1 or later (MB-SEC-006) |

## Run-as identity

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| With client credentials, the effective user is the run-as user configured on the connected app or external client app, not anything in the Mule configuration | All | Documented for connected apps: [client credentials setup](https://help.salesforce.com/s/articleView?id=xcloud.connected_app_client_credentials_setup.htm&type=5) (Edit Policies, Client Credentials Flow, Run As), which recommends a run-as user with the API Only User permission. External client apps: Unverified | The setup page for the app type in use |
| An administrator can change the run-as user with no code or deployment change, so the effective identity can change underneath a running app | All | Observed: the run-as user changed between two integration users on the same day with no Mule change | Identity verification below, after every change window |

## Account and licence limits

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| Users on the Salesforce Integration user licence cannot access Salesforce through any user interface; for REST access Salesforce directs you to an external client app with an OAuth 2.0 flow | All | Documented: [Integration user](https://help.salesforce.com/s/articleView?id=platform.integration_user.htm&type=5) | Same page |
| Username and password logins are being retired: Salesforce recommends against the OAuth username-password flow and suggests blocking it, and connector 12.0.0 removed that connection type. A password login for an integration user also failed in practice | All | Documented: [username-password flow](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&type=5), 12.0.0 release notes; Observed | Both pages |

## Sources

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| Replay options: `ONLY_NEW` receives only events broadcast after subscribing; `ALL` includes stored events within retention; `FROM_REPLAY_ID` resumes after a given id; `FROM_LAST_REPLAY_ID` uses the highest id in the object store whether or not it was processed successfully | Current reference | Documented: [connector reference](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-reference) Replay Option | Reference page for the installed major |
| With `autoReplay="true"` ("Replay Failed Events If Any or Resume from Last Replay Id") the Replay topic and channel listeners resume after a restart from the last successfully processed event, or from the lowest failed replay id; the ids are kept in an object store for 72 hours. Without it, `ONLY_NEW` loses every event published while the app is stopped, restarting or redeploying, including on a channel that has received nothing since boot | Current reference | Documented: [processing events, resume from the last replay id](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-processing-events#resume-from-the-last-replay-id) and the connector reference; Observed: events lost after a restart with `ONLY_NEW` and auto replay off | Check `autoReplay` on every Replay listener; publish a test event during a stop, then restart |
| The resume state is keyed by the username in the connector configuration. Changing the integration user, or moving to a connection type without a username such as client credentials, can therefore start from an empty resume state | Current reference | Documented mechanism: [processing events](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-processing-events#resume-from-the-last-replay-id); the effect for client credentials is Unverified | Before the switch, stop publishers or accept a replay gap; after it, confirm the first events resume from the expected position |
| `FROM_LAST_REPLAY_ID` stores the position before processing outcome is known, so a failed event is not replayed automatically; pair it with error handling that records failures | Current reference | Documented, same row as above | Same |
| Within a running app, an `ONLY_NEW` listener resumes each channel from the last replay id it received after the periodic `403::Unknown client` reconnect, so no gap appears. Across an app start each channel begins at the newest event, and because the id advances on receipt, work queued in memory when the app stops is lost too. Reconcile the start gap after every start, or use `autoReplay` with idempotent consumers | 11.x | Observed: no gap across reconnects, a gap after each start, on production subscription apps | Publish a test event during a stop; compare publisher timestamps with the first processed event after start |
| Replay retention depends on the event type: 72 hours for high-volume platform events and change data capture, 24 hours for PushTopic, generic and standard-volume events. The connector reference's "24-hour" wording is out of date for high-volume events. Events older than retention are gone whatever the option | Salesforce side | Documented: [Streaming API durability](https://developer.salesforce.com/docs/platform/api-streaming/guide/using-streaming-api-durability.html) | Same page |
| Streaming listeners renew their tokens across reconnects; a client credentials subscriber stayed subscribed through repeated reconnects | 11.x | Observed: a non-production app with client credentials over two days | Watch the first reconnects after a change; events keep arriving |
| Never deploy streaming listeners with a rolling update: old and new replicas both subscribe and every event of the overlap is processed twice, and their combined calls can exceed the org's or a backend's concurrency limit. On CloudHub 2.0 use stop-start or the recreate deployment model | All | Observed: rolling overlapped 7 to 32 s; recreate and stop-start never overlapped (measured on a sandbox, 2026-10-26; see [safe change](../../mule-ops/references/safe-change.md#choose-the-deployment-mode)); semantics documented in [CloudHub 2.0 updates](https://docs.mulesoft.com/cloudhub-2/ch2-update-apps) | Replica start and stop times against duplicate timestamps |
| With more than one worker, the Replay topic and channel listeners process every message on every instance. Run them on a single worker (or primary node only, where clustering applies) and hand work to other workers through a shared queue | Current reference | Documented: [processing events](https://docs.mulesoft.com/salesforce-connector/latest/salesforce-connector-processing-events) | Replica count of any app with a Replay listener |

## Known signatures

| Signature | Benign while | Stops being benign when | Evidence |
| --- | --- | --- | --- |
| Periodic CometD reconnect with `403::Unknown client`, plus a `DefaultSystemExceptionStrategy` ERROR logged with it (observed roughly hourly) | The handshake and resubscribe succeed and events keep arriving after it | Events stop after the reconnect, the reconnect repeats in a tight loop, or authentication errors follow it | Documented: Salesforce removes client state after a timeout and answers `403::Unknown client` with advice to handshake again ([handling errors](https://developer.salesforce.com/docs/platform/api-streaming/guide/streaming-handling-errors.html), [timeouts](https://developer.salesforce.com/docs/platform/api-streaming/guide/using-streaming-api-timeouts.html)). Connector recovery was added in 10.22.5, and 11.3.3 fixed a connection leak in the Replay Channel Listener during 403/401 recovery, so use 11.3.3 or later. Observed: the paired ERROR line on 11.x |

| A single `503::Server is too busy` on subscribe that is followed by a successful subscribe | The channel subscribes on the next attempt and events arrive | It repeats, or a channel stays unsubscribed after start | Observed on 11.x after app starts |
| `INVALID_SESSION_ID` on the first use of freshly issued client credentials tokens, for a period after issue | Old and new app versions fail the same way and it clears without a change | It persists, or only the new version fails | Observed: a refusal window of roughly 20 minutes affecting the previous and new release alike; the cause was outside the release, so a rollback would only have added a restart. Map it to a retryable status for callers (Class D in `mule-development`), never to a permanent 4xx |

Count these lines separately from application errors in health reports, with the criteria above.

## Sensitive loggers

| Category | Risk | Evidence |
| --- | --- | --- |
| `org.mule.extension.salesforce.internal.service.streaming` and the streaming transport beneath it | At DEBUG they log session identifiers and authorization headers, which are usable credentials | Observed: a diagnostic release raised the streaming package to DEBUG in production; it was rolled back within minutes and the session revoked, and the lines stayed readable for the log retention |

Never set them to DEBUG or TRACE in a shared environment; mule-lint flags sensitive loggers in
`log4j2.xml` (`LOG-007`). If streaming must be debugged, do it on a private non-production app, then rotate the
session by restarting and remove the logs. After any logging change, run
`scan_logs_for_credentials` on the new logs before calling the deployment healthy; it returns marker
counts, never the lines.

## Identity verification

After any change to the connection type, client application or run-as user:

1. Query `LoginHistory` for the integration user around the change time and read **`LoginSubType`**,
   which names the flow: `OauthClientCredentials` for client credentials, `OauthUsernamePassword`
   for the OAuth username-password flow. `LoginType` alone is not enough: `Remote Access 2.0`
   (`Oauth2`) covers every OAuth 2.0 flow
   ([LoginHistory](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_loginhistory.htm)).
2. Call the identity URL returned with the token (`id`), or the
   [UserInfo endpoint](https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_using_userinfo_endpoint.htm&type=5)
   on the My Domain host, with the access token, and compare the user with the expected
   integration user.
3. Record the result by role ("the integration user"), never by user name.

## Non-blocking warnings

| Message | Meaning | Evidence |
| --- | --- | --- |
| "API version lower than recommended (65.0)" | The configured API version is older than the connector recommends; the connection still works | Observed on 11.x |

Move the API version deliberately: Basic Authentication stops working above v64.0, so raising the
version and keeping Basic Authentication breaks the login.

## Changing the integration user

Before switching, list what depends on the running user, then check each one:

- validation rules that test `$Profile` or `$User` fields
- Flows and other automation that read running-user fields or run only for certain users
- owner and created-by on records the integration creates, and any assignment logic based on them
- sharing rules, permission sets and permission set groups held by the old user
- reports, dashboards and audit filters keyed to the old user
- the Replay listeners' stored resume state, which is keyed by the configured username (see
  [Sources](#sources))

Then follow [safe change](../../mule-ops/references/safe-change.md) for the deployment and the
post-change checks.
