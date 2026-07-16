# OAuth `expires_in` String Compatibility Design

## Problem

Exact's OAuth token endpoint can return `expires_in` as a JSON string such as
`"600"`. The current validation rejects all strings, which makes an otherwise
valid authorization-code exchange fail.

## Decision

Accept only ASCII decimal-integer strings in addition to existing numeric JSON
values. Convert accepted strings to `float` before applying the existing
positive, finite, 24-hour maximum validation. Continue rejecting whitespace,
signs, decimals, exponent notation, booleans, empty strings, and out-of-range
values.

## Testing

Add a regression test that exchanges an authorization code using
`"expires_in": "600"` and confirms the resulting token expiry. Keep the
existing malformed-value parametrization, changing its `"600"` case to an
actually malformed numeric string.
