---
title: "5. OpenID Connect and Single Sign-On"
description: "OIDC, the identity layer on top of OAuth 2.0: ID tokens, discovery, JWKS and key rotation, nonce vs state vs PKCE, UserInfo, SSO and logout, OIDC vs OAuth 2.0 vs SAML, the attacks, and interview questions."
---

# OpenID Connect and Single Sign-On

"Sign in with Google", "Log in with your company account", one login that works across Gmail, Drive and YouTube: all of these are **OpenID Connect (OIDC)**. It is the protocol behind almost every modern single sign-on (SSO), and it is the part of API security that interviewers use to check whether you really understand OAuth 2.0 or just memorised the flow.

This guide assumes you have read §1 of [Cross-Cutting Concerns](03_cross_cutting_concerns.md) (JWTs and the OAuth 2.0 authorization code + PKCE flow). The runnable version of everything below is `REST/labs/golang/09_oidc_login_id_token_jwks`: a tiny identity provider and an app that logs in against it, with the attacks tried for real.

## 1. The Problem OIDC Solves

OAuth 2.0 answers **"may this app act on my behalf?"** It hands the app an **access token**: a key to an API. It deliberately says nothing about *who* the user is. The access token is meant for the API, not for the app; the app is not even supposed to look inside it (it may be opaque).

Around 2010 every provider bolted its own "who is this?" onto OAuth: call `GET /me` with the access token and read the user id. That "OAuth for login" pattern is broken:

*   **Token substitution.** A malicious app that you once logged into gets an access token for *your* account. It replays that token to a victim app that uses "OAuth for login". The victim calls `/me`, sees your id, and logs the attacker in **as you**. The access token carried no statement "this was issued for app X", so the victim cannot tell.
*   **Every provider was different**, so every integration was custom code.

**OpenID Connect 1.0** (OpenID Foundation, 2014) fixes this with one addition: alongside the access token, the authorization server also returns an **ID token**, a signed JWT that states *who* logged in, *when*, *how*, *which issuer* says so, and *for which app* (`aud`). The app validates it locally. Nothing else in OAuth changes: same endpoints, same grants, same PKCE.

> **One sentence for interviews:** OAuth 2.0 is about *authorization* (delegated access to an API); OIDC is a thin *authentication* layer on top of it that adds the ID token, a standard `UserInfo` endpoint, standard scopes and claims, and discovery.

## 2. OAuth 2.0 vs OIDC vs SAML

| | OAuth 2.0 | OpenID Connect | SAML 2.0 |
| :--- | :--- | :--- | :--- |
| Answers | "May this app call this API for me?" | "Who is this user, and did they just log in?" | "Who is this user?" (enterprise SSO) |
| Main artefact | Access token (opaque or JWT), for the **API** | **ID token** (always a JWT), for the **app** | Signed XML **assertion** |
| Audience of the artefact | Resource server | Client (relying party) | Service provider |
| Transport | JSON over HTTPS, redirects | Same as OAuth 2.0 | XML via browser POST/redirect bindings |
| Mobile / SPA / API friendly | Yes | Yes | Poorly (XML, browser POST) |
| Typical use | Third-party API access, machine-to-machine | Consumer login, workforce SSO, mobile apps | Legacy and enterprise workforce SSO |
| Discovery | RFC 8414 metadata | `/.well-known/openid-configuration` | Metadata XML |

Rule of thumb: build new things on OIDC. Support SAML when an enterprise customer's IdP only speaks SAML (common in B2B SaaS; that is why "SAML SSO" is still a paid enterprise tier in many products).

## 3. Vocabulary

| Term | Meaning |
| :--- | :--- |
| **OP** (OpenID Provider) / **IdP** | The authorization server that also authenticates users: Google, Microsoft Entra ID, Okta, Auth0, Keycloak |
| **RP** (Relying Party) | Your app, the OAuth *client* that relies on the OP to say who the user is |
| **ID token** | A signed JWT **for the RP** describing the authentication event |
| **Access token** | A token **for an API** (possibly the OP's own UserInfo endpoint) |
| **Refresh token** | Long-lived credential to get new access (and sometimes ID) tokens without the user |
| **UserInfo endpoint** | OAuth-protected API at the OP that returns profile claims |
| **Claims** | Name/value facts about the user: `sub`, `email`, `name`, `email_verified` |
| **Scopes** | `openid` (required: turns an OAuth request into an OIDC request), `profile`, `email`, `address`, `phone`, `offline_access` (ask for a refresh token) |
| **`iss` + `sub`** | The user's stable, unique identity. `sub` is unique only *within* an issuer, so store the pair |

## 4. The ID Token

A decoded ID token (header and payload of a JWS):

```json
{ "alg": "RS256", "kid": "2026-09-key-b", "typ": "JWT" }
```

```json
{
  "iss": "https://login.example.com",
  "sub": "248289761001",
  "aud": "shop-web",
  "exp": 1790000600,
  "iat": 1790000000,
  "auth_time": 1789999990,
  "nonce": "n-0S6_WzA2Mj",
  "acr": "urn:example:mfa",
  "amr": ["pwd", "otp"],
  "sid": "08a5019c-17e1-4977-8f42-65a12843ea02",
  "at_hash": "77QmUPtjPfzWtF2AnpK9RQ",
  "email": "ada@example.com",
  "email_verified": true
}
```

| Claim | Meaning | Why it matters |
| :--- | :--- | :--- |
| `iss` | Issuer URL | Must be exactly the OP you started the login with |
| `sub` | Subject: stable user id at this issuer | Your user key is `(iss, sub)`, never the email |
| `aud` | Client id(s) the token is for | Stops a token minted for another app being replayed at yours |
| `exp`, `iat` | Expiry, issue time | Short lived (minutes). Allow a small clock skew (≈ 1-5 min) |
| `nonce` | Echo of the value the RP sent in the auth request | Binds the token to *this* browser's login attempt (replay protection) |
| `auth_time` | When the user actually typed credentials | Enforce "re-authenticate within 5 minutes" for sensitive actions (`max_age`) |
| `acr`, `amr` | Assurance level, methods used (`pwd`, `otp`, `hwk`, `face`) | Step-up: require MFA before a payout |
| `azp` | Authorized party | Needed when `aud` has several values |
| `at_hash`, `c_hash` | Hash of the access token / code | Binds the token to the access token or code issued with it (hybrid and implicit flows) |
| `sid` | OP session id | Used by back-channel logout to say which session ended |

### Validating an ID token, in order

OIDC Core §3.1.3.7 lists the checks. The order matters: do the cheap, structural ones first and **never read the claims before the signature is verified**.

1.  Parse the three base64url parts. Reject anything that is not a JWS (an encrypted JWE is only allowed if you registered for it).
2.  **`alg`** must be one you expect for this OP (usually `RS256` or `ES256`). Reject `none`. Never let the token choose between symmetric and asymmetric (the RS256 → HS256 "algorithm confusion" attack uses the public key as an HMAC secret).
3.  Find the key by **`kid`** in the OP's JWKS, then **verify the signature**.
4.  **`iss`** equals the issuer from discovery, exactly (scheme, host, path, no trailing-slash differences).
5.  **`aud`** contains your `client_id`. If it has several audiences, `azp` should be present and equal your `client_id`.
6.  **`exp`** is in the future, **`iat`** is not absurdly old or in the future (allow a small skew).
7.  **`nonce`** equals the one you stored in the user's session for this login, then delete it (one use).
8.  If you asked for `max_age` or `acr_values`, check `auth_time` and `acr`.
9.  If an access token came with it and `at_hash` is present, check it: base64url of the left half of `SHA-256(access_token)` for `RS256`.

Libraries do all of this (`coreos/go-oidc`, `authlib`, `oidc-client-ts`, Spring Security, `Microsoft.Identity.Web`). The interview is about knowing *why* each check exists.

## 5. Discovery and JWKS

An RP needs a lot of configuration: where to send the user, where to swap the code, which keys sign tokens, which algorithms are used. OIDC Discovery puts all of it at one well-known URL:

```http
GET /.well-known/openid-configuration HTTP/1.1
Host: login.example.com
```

```json
{
  "issuer": "https://login.example.com",
  "authorization_endpoint": "https://login.example.com/authorize",
  "token_endpoint": "https://login.example.com/token",
  "userinfo_endpoint": "https://login.example.com/userinfo",
  "jwks_uri": "https://login.example.com/.well-known/jwks.json",
  "end_session_endpoint": "https://login.example.com/logout",
  "response_types_supported": ["code"],
  "subject_types_supported": ["public", "pairwise"],
  "id_token_signing_alg_values_supported": ["RS256", "ES256"],
  "scopes_supported": ["openid", "profile", "email", "offline_access"],
  "code_challenge_methods_supported": ["S256"],
  "backchannel_logout_supported": true
}
```

**Rule:** the `issuer` inside the document must equal the URL you fetched it from (minus the well-known suffix), and every ID token's `iss` must equal that `issuer`. This is what stops one OP impersonating another.

The **JWKS** (JSON Web Key Set, RFC 7517) is the OP's public signing keys:

```json
{ "keys": [
  { "kty": "RSA", "kid": "2026-09-key-b", "use": "sig", "alg": "RS256", "n": "0vx7ago...", "e": "AQAB" },
  { "kty": "RSA", "kid": "2026-06-key-a", "use": "sig", "alg": "RS256", "n": "xjlCRBq...", "e": "AQAB" }
]}
```

### Key rotation without downtime

1.  The OP **publishes** the new key in the JWKS days before using it (old and new both listed).
2.  RPs cache the JWKS (honour `Cache-Control`; hours is typical).
3.  The OP **starts signing** with the new `kid`.
4.  An RP that sees an unknown `kid` **refetches the JWKS once** (rate-limited, so an attacker spraying random `kid`s cannot make you hammer the OP), then retries the lookup.
5.  After the longest token lifetime has passed, the OP **removes** the old key.

A signing-key compromise is handled the same way, only faster: remove the key immediately, and tokens signed with it stop validating.

## 6. The Authorization Code Flow with PKCE

This is the one flow to know. It is identical to the OAuth 2.0 flow in [Cross-Cutting Concerns](03_cross_cutting_concerns.md), plus `scope=openid`, a `nonce`, and an `id_token` in the token response.

```mermaid
sequenceDiagram
    participant B as Browser
    participant RP as App (RP backend)
    participant OP as OpenID Provider
    participant API as Your API
    B->>RP: GET /login
    RP->>RP: make state, nonce, code_verifier; store in session
    RP-->>B: 302 to OP /authorize?response_type=code&client_id&redirect_uri&scope=openid email&state&nonce&code_challenge
    B->>OP: GET /authorize ...
    OP->>B: login page (skipped if OP session cookie exists = SSO)
    B->>OP: credentials + MFA
    OP-->>B: 302 to redirect_uri?code=...&state=...&iss=...
    B->>RP: GET /callback?code&state&iss
    RP->>RP: check state (CSRF) and iss (mix-up)
    RP->>OP: POST /token code, code_verifier, client auth
    OP-->>RP: id_token, access_token, refresh_token
    RP->>RP: validate id_token (sig via JWKS, iss, aud, exp, nonce)
    RP-->>B: Set-Cookie: session=... (HttpOnly, Secure, SameSite=Lax)
    RP->>API: Authorization: Bearer access_token
```

Three random values, three different attacks. Interviewers love this table:

| Value | Created by | Checked by | Stops |
| :--- | :--- | :--- | :--- |
| `state` | RP, stored in the browser session | RP, on the callback | **Login CSRF**: an attacker making your browser finish *their* login, so you end up in their account |
| `nonce` | RP, stored in the session | RP, inside the **ID token** | **ID token replay / injection**: a token from another login attempt being accepted |
| PKCE `code_verifier` | RP, hashed into `code_challenge` | **OP**, at `/token` | **Code interception / injection**: a stolen code being redeemed by someone who lacks the verifier |

PKCE was invented for mobile apps but the OAuth 2.0 Security BCP (RFC 9700, January 2025) recommends it for **every** client, confidential ones included. With PKCE the `nonce` is still required by OIDC for the implicit/hybrid flows and remains good defence-in-depth for the code flow; send both.

Also check the **`iss` parameter** in the authorization response (RFC 9207) when you talk to more than one OP: it defeats the **mix-up attack**, where a malicious OP tricks your app into sending a code from an honest OP to the attacker's token endpoint.

## 7. UserInfo

`GET /userinfo` with the access token returns profile claims as JSON (or a signed JWT if registered).

```http
GET /userinfo HTTP/1.1
Host: login.example.com
Authorization: Bearer SlAV32hkKG
```

```json
{ "sub": "248289761001", "name": "Ada Lovelace", "email": "ada@example.com", "email_verified": true }
```

*   **The `sub` from UserInfo must equal the ID token's `sub`**, or you must discard the response (a substituted access token would otherwise mix two users).
*   Use it when the ID token is kept small (many OPs only put `sub` in it) or to refresh profile data later.
*   The UserInfo response is only as trustworthy as the TLS connection that fetched it; the ID token is signed and can be verified offline. Authentication decisions come from the ID token.

## 8. The Other Flows

| Flow | Status (2026) | Notes |
| :--- | :--- | :--- |
| **Authorization code + PKCE** | Use it | Web apps, SPAs (ideally through a backend), mobile, desktop |
| **Implicit** (`response_type=id_token token`) | Do not use | Tokens in the URL fragment leak via history and referrers. RFC 9700 says no; OAuth 2.1 (draft) removes it |
| **Hybrid** (`code id_token`) | Rare | Gets an ID token from the front channel early; `c_hash` binds it to the code |
| **Resource owner password** | Do not use | The app sees the password; no MFA, no SSO. Removed in OAuth 2.1 |
| **Client credentials** | Use for machine-to-machine | **No user, so no ID token and no OIDC.** Pure OAuth |
| **Device authorization** (RFC 8628) | Use for TVs, CLIs | "Go to example.com/device and enter ABCD-EFGH"; can return an ID token |
| **CIBA** | Niche | Decoupled login, e.g. a bank approves a call-centre request on your phone |

## 9. Single Sign-On: How It Actually Works

SSO is not a separate protocol. It falls out of one fact: **the OP keeps its own login session** (a cookie on the OP's domain). When a second app sends you to the OP, the OP sees the cookie and immediately redirects back with a code. No password prompt.

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as App A (mail)
    participant C as App B (drive)
    participant OP as OpenID Provider
    B->>A: open mail.example.com
    A-->>B: 302 to OP /authorize (client_id=mail)
    B->>OP: /authorize (no OP cookie yet)
    OP->>B: login form, user signs in
    OP-->>B: Set-Cookie: op_session ; 302 back to mail with code
    B->>A: /callback, A swaps code, sets its own session
    B->>C: later: open drive.example.com
    C-->>B: 302 to OP /authorize (client_id=drive)
    B->>OP: /authorize with op_session cookie
    OP-->>B: 302 back to drive with code (no prompt)
    B->>C: /callback, C swaps code, sets its own session
```

There are **three kinds of session**, and most SSO bugs come from forgetting one:

1.  The **OP session** (cookie on `login.example.com`).
2.  Each **RP session** (cookie on `mail.example.com`, `drive.example.com`), created after the ID token is validated.
3.  The **tokens** (access/refresh) the RPs hold for calling APIs.

Useful request parameters: `prompt=none` (silent login: fail with `login_required` instead of showing a page), `prompt=login` (force re-authentication), `max_age=300` (credentials typed at most 5 minutes ago), `login_hint=ada@example.com`, `acr_values` (ask for MFA).

### Logout is the hard part

Logging out of app B does not end the OP session or app A's session. OIDC has three optional specs:

| Mechanism | How it works | Trade-off |
| :--- | :--- | :--- |
| **RP-Initiated Logout** | RP redirects to `end_session_endpoint?id_token_hint=...&post_logout_redirect_uri=...` | Ends the OP session; other RPs are not told by this alone |
| **Front-Channel Logout** | OP renders hidden iframes that load each RP's logout URL | Needs third-party cookies inside the iframes, which Safari and Firefox block by default: unreliable |
| **Back-Channel Logout** | OP POSTs a signed **logout token** (JWT with `sid` and/or `sub`, an `events` claim, no `nonce`) straight to each RP's backend | Reliable; the RP must map `sid` to its own sessions and kill them |

For workforce SSO, prefer back-channel logout and short RP sessions. Also, removing someone from the company should revoke them in the IdP *and* deprovision them in each app; that is what **SCIM** (user provisioning) is for.

## 10. Where the Tokens Live in a Browser App

```arch
%% caption: The backend-for-frontend pattern: tokens stay on the server, the browser only holds an HttpOnly session cookie.
group br "Browser" color=slate icon=browser
node spa "SPA" at 0,0 in br icon=browser sub="no tokens in JS"
group srv "Your backend (trust boundary)" color=blue icon=shield
node bff "BFF / RP" at 1,0 in srv icon=server sub="holds tokens"
node api "Orders API" at 1,1 in srv icon=api sub="checks access token"
node op "OpenID Provider" at 2,0 icon=identity sub="login, /token, JWKS"
spa -> bff : "session cookie"
bff -> op : "code + verifier"
bff -> api : "Bearer token"
api ..> op : "JWKS (cached)"
```

*   **Backend-for-frontend (BFF), recommended.** The server-side RP does the code exchange, keeps the tokens, and gives the browser an `HttpOnly; Secure; SameSite` session cookie. XSS cannot steal a token that JavaScript never sees.
*   **Pure SPA holding tokens.** Works (code + PKCE, public client) but any XSS can exfiltrate the tokens. If you must, keep access tokens in memory, use short lifetimes and refresh-token rotation, and consider sender-constrained tokens (DPoP, RFC 9449).
*   **Never** put tokens in `localStorage` "because it is easy", and never in URLs.

## 11. APIs Take Access Tokens, Not ID Tokens

The single most common OIDC mistake in API code:

*   The **ID token** is addressed to the **app** (`aud = client_id`). It proves a login happened. Sending it to your API as a bearer token means the API accepts a credential that was never meant for it, has no scopes, and was issued to a different audience.
*   The **access token** is addressed to the **API** (`aud = https://api.example.com`), carries scopes, and is what `Authorization: Bearer` should carry. If it is a JWT, validate it per RFC 9068 (JWT profile for access tokens: `typ: at+jwt`, `iss`, `aud`, `exp`, `scope`, `client_id`).
*   Service A calling service B on the user's behalf should **exchange** the token for one with B's audience (RFC 8693 token exchange) rather than forwarding its own.

## 12. Attacks and Pitfalls

1.  **Using `email` as the user key.** Emails change and get reassigned; some IdPs let users set an unverified email (the 2023 "nOAuth" issue with a mutable email claim in Microsoft Entra ID multi-tenant apps). Key on `(iss, sub)`; link accounts by email only when `email_verified` is true *and* you trust that issuer for that domain.
2.  **Not checking `aud`.** Any token from the same OP for any app logs users into yours (the token substitution attack from §1, back again).
3.  **Accepting `alg: none` or letting the token pick the algorithm.** Pin the algorithm per issuer.
4.  **Skipping `state`** (login CSRF) or **`nonce`** (token replay).
5.  **Loose `redirect_uri` matching** (prefix or wildcard). An open redirect on your domain then leaks codes. OPs must match exactly; register exact URIs.
6.  **Fetching the JWKS on every request**, or **never refetching** (breaks on key rotation). Cache, and refetch on unknown `kid` with a rate limit.
7.  **Treating the ID token as a session.** It expires in minutes; after validation, create your own session. Do not refresh your session by "refreshing the ID token" in the browser.
8.  **Multi-tenant IdPs** (Entra ID "common" endpoint, Google for any domain): `iss` differs per tenant, so validate the tenant (`tid`, `hd`) you actually allow, or anyone with an account at that IdP can sign in.

## 13. Check Yourself

> ❓ **Question 1:** Your app does "Sign in with X" by calling X's `/me` endpoint with the access token. What attack is this open to, and how does OIDC fix it?
>
> ❓ **Question 2:** Explain what `state`, `nonce` and PKCE each protect against. If you use PKCE, can you drop `state`?
>
> ❓ **Question 3:** Your API receives an ID token as a bearer token. Should it accept it?
>
> ❓ **Question 4:** The IdP rotated its signing key and half your pods started rejecting logins for an hour. What went wrong and how should the RP handle keys?
>
> ❓ **Question 5:** A user logs out of one app but is still logged into three others. Why, and what would you implement?
>
> ❓ **Question 6:** Why is `sub` alone not a safe primary key for users in a multi-IdP app?

**Answers**

1.  Token substitution: a token issued to a *different* app for the same user is replayed at yours and `/me` happily returns the victim's id. OIDC's ID token carries `aud` (your client id) and `nonce` (this login attempt) and is signed by the OP, so a token for another app or another attempt fails validation.
2.  `state` stops login CSRF (checked by the RP on the callback), `nonce` stops ID-token replay (checked by the RP inside the token), PKCE stops a stolen code from being redeemed (checked by the OP at `/token`). RFC 9700 allows PKCE to replace `state` for CSRF protection *if* the RP is sure the OP enforces PKCE, but `state` also carries app state and costs nothing, so keep it.
3.  No. The ID token's audience is the client app, not the API, and it has no scopes. The API should require an access token with its own `aud`, and validate `iss`, `aud`, `exp` and scopes.
4.  The pods cached the JWKS and did not refetch on an unknown `kid` (or cached it with a long fixed TTL). Refetch on unknown `kid` (rate-limited), honour `Cache-Control`, and expect the OP to pre-publish new keys.
5.  Each app has its own session plus the OP's session; logging out of one ends only that one. Use RP-initiated logout to end the OP session and back-channel logout so the OP tells every RP to drop sessions for that `sid`/`sub`; keep RP sessions short.
6.  `sub` is only unique within one issuer. Two IdPs can both issue `sub=12345` for different people. Key users on `(iss, sub)`.

## 14. Where It Is Practised

| Topic | Lab |
| :--- | :--- |
| Discovery, JWKS, code + PKCE, `state`, `nonce`, ID-token validation, UserInfo `sub` check, key rotation, and the attacks (`alg=none`, wrong `aud`, replayed `nonce`, forged key) | `REST/labs/golang/09_oidc_login_id_token_jwks` |
| JWT signing and validation from scratch, `401` vs `403` | [Jwt auth and scopes](../REST/labs/python/03_jwt_auth_and_scopes.py) |
| Bearer tokens, the basics | `REST/Foundation/*/09_authentication_bearer_tokens` |
