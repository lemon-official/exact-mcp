# Interactive OAuth CLI Design

## Goal

Make Exact Online authorization reliable from one interactive command, explicitly verify encrypted refresh-token persistence, expose safe conditional refresh, and report access-token expiry as relative time.

## CLI behavior

`exact-mcp auth` composes the existing authorization URL and code-exchange flows. It prints the Exact authorization URL and CSRF state, prompts for the complete callback URL, extracts the `code` query parameter, HTML-decodes it, exchanges it, and saves the complete token pair to the configured encrypted token file.

The existing `auth-url` and `exchange-code` commands remain available for scripts and manual workflows. Code exchange also HTML-decodes its input so both entry points handle Exact callback encoding consistently.

`exact-mcp auth-refresh` conditionally refreshes stored credentials. It never refreshes a token younger than Exact's 570-second minimum age and reports the token age and remaining wait. Once eligible, it refreshes only when the access token is within the configured expiry skew. Otherwise it reports the remaining access-token lifetime. A successful refresh atomically persists the returned access token and rotated refresh token; if Exact omits a rotated refresh token, the existing one is preserved.

`exact-mcp auth-status` reports access-token expiry relative to the current time, using output such as `expires in 8m 12s` or `expired 45s ago`, instead of exposing a Unix timestamp.

## Components and data flow

A small callback parsing helper validates that the pasted value is a URL and contains exactly one non-empty `code` query parameter. Standard URL parsing performs percent-decoding, followed by `html.unescape` for HTML entities.

`OAuthManager` owns refresh eligibility and timing decisions so CLI behavior cannot diverge from server-side automatic refresh behavior. A structured refresh result distinguishes refreshed, too young, and not due outcomes without exposing any credential values.

`EncryptedFileTokenStore` remains the only persistence mechanism. Access and refresh tokens stay together in the encrypted `OAuthTokens` payload and are never printed or logged.

## Errors and security

Missing or malformed callback URLs produce an actionable authorization failure without making a token request. Missing stored credentials instruct the user to run `exact-mcp auth`. OAuth endpoint errors retain the existing sanitized error behavior.

The callback code, access token, refresh token, client secret, encryption key, and decrypted token payload are never included in CLI output or logs.

## Testing

Tests cover callback extraction and HTML decoding, malformed callbacks, the interactive `auth` flow, encrypted persistence with a decrypted assertion for the refresh token, refresh-token rotation, preservation when a refresh response omits a new token, the 570-second minimum-age message, not-due behavior, successful near-expiry refresh, and relative status formatting for future and expired tokens.
