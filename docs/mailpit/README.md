# Mailpit local email verification

Mailpit is the local SMTP inbox for Matchmaker development. It receives verification and password-reset messages without sending anything to real email addresses.

The current Compose configuration is:

- API SMTP host: `mailpit`
- SMTP port inside Compose: `1025`
- Mailpit web inbox: <http://localhost:8025>
- API address: <http://127.0.0.1:8000>
- Development sender: `noreply@matchmaker.local`

Match, like, project-join and chat notifications are in-app notifications in the MVP. They do not appear in Mailpit. Mailpit is used for account verification and password-reset email flows.

## Start the local stack

From PowerShell, run these commands from the `backend` directory:

```powershell
Set-Location backend
Copy-Item .env.example .env
```

Open `backend/.env` and set local-only values. The Compose file requires both variables:

```dotenv
POSTGRES_PASSWORD=local-dev-only
JWT_SECRET=local-dev-secret-change-me-12345678901234567890
```

Do not commit `.env` or use these values in production.

Start the database, Redis, Mailpit and API:

```powershell
docker compose up -d db redis mailpit api
docker compose ps
```

Open the inbox:

```powershell
Start-Process http://localhost:8025
```

The API container is configured to use `MAIL_MODE=smtp`, `MAIL_SERVER=mailpit` and `MAIL_PORT=1025`. The browser uses port `8025` for the Mailpit UI; it is not the SMTP port.

## Verify a new account

Use a test address. It does not need to be a real mailbox because Mailpit captures the message locally.

```powershell
$registration = @{
  username = "mailpit-user"
  email = "mailpit-user@example.test"
  password = "LocalTest123!"
  mode = "developer"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/register `
  -ContentType "application/json" `
  -Body $registration
```

In Mailpit:

1. Search for `mailpit-user@example.test`.
2. Open the newest Matchmaker message.
3. Confirm the sender is `noreply@matchmaker.local`.
4. Copy the six-digit verification code from the message.

Verify the code through the API:

```powershell
$verification = @{
  email = "mailpit-user@example.test"
  code = "123456"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/verify-email `
  -ContentType "application/json" `
  -Body $verification
```

Replace `123456` with the code shown in Mailpit. Use `mode = "project"` instead when testing the project onboarding path. After a successful response, the account can log in and is redirected to the selected setup form.

## Verify the planned link flow

Phase 1 will include both a six-digit code and a verification link in the email. The link token will be single-use and valid for 24 hours. The code remains valid for 10 minutes with at most five failed attempts.

When the link endpoint is implemented, test it by:

1. Registering a fresh test account.
2. Opening the newest message in Mailpit.
3. Clicking the verification link or copying its token into the verification form.
4. Confirming that a second use of the same link is rejected.
5. Waiting for or simulating expiry and confirming the expired link is rejected.

## Test resend and password reset

Resend verification for an unverified account:

```powershell
$email = @{ email = "mailpit-user@example.test" } | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/resend-verification `
  -ContentType "application/json" `
  -Body $email
```

The newest message should contain the usable credentials. Older verification credentials must no longer work after the Phase 1 resend behavior is implemented.

Request a password-reset code:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/forgot-password `
  -ContentType "application/json" `
  -Body $email
```

Password-reset messages should be checked in the same Mailpit inbox. The API must return an enumeration-safe response whether or not the address exists.

## Troubleshooting

### The inbox is empty

Check that all services are running:

```powershell
docker compose ps
docker compose logs api --tail 100
docker compose logs mailpit --tail 100
```

The API must use `MAIL_SERVER=mailpit` and `MAIL_PORT=1025` inside Compose. `localhost:1025` is incorrect from inside the API container.

### The API is not reachable

Check <http://127.0.0.1:8000/health> and inspect the API logs. The API depends on PostgreSQL, Redis and Mailpit startup.

### The message shows the wrong recipient or sender

The recipient is the `email` submitted during registration. The sender is the `MAIL_FROM` value supplied to the API container. In the default Compose setup it is `noreply@matchmaker.local`.

### Stop the local stack

```powershell
docker compose stop
```

Use `docker compose down` only when the containers should be removed. Do not use `down --volumes` unless local database data is intentionally disposable.
