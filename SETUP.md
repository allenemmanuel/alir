# Setup: website editor (one-time)

This takes about 30 minutes and is done once by the developer. After this, the
client only uses the editor described in HANDOVER.md.

The website is hosted on Firebase (project `alir-80c4f`, site `alirsabah`).
Edits are saved to GitHub (repository `allenemmanuel/alir`), and GitHub
Actions rebuilds and publishes the site automatically.

## 1. Create a GitHub sign-in app

1. On GitHub, go to **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. Fill in:
   - **Application name:** ALIR website editor
   - **Homepage URL:** `https://alirsabah.web.app`
   - **Authorization callback URL:** `https://<your-helper-address>/callback`
     (you will know this address after step 2; come back and edit this field)
3. Click **Register application**. Copy the **Client ID**.
4. Click **Generate a new client secret** and copy it. Keep it private.

## 2. Publish the sign-in helper (Cloudflare Workers, free)

1. Sign up at cloudflare.com (free) and go to **Workers & Pages → Create → Worker**.
2. Name it `alir-editor-login` and click **Deploy**.
3. Click **Edit code**, delete the sample code, paste the contents of
   `oauth-proxy/worker.js`, and click **Deploy**.
4. Go to **Settings → Variables and Secrets** and add:
   - `GITHUB_CLIENT_ID`: the Client ID from step 1 (plain text)
   - `GITHUB_CLIENT_SECRET`: the client secret from step 1 (encrypted)
   - `SITE_ORIGIN`: `https://alirsabah.web.app` (plain text)
5. Your helper address is shown on the Worker page, like
   `https://alir-editor-login.<your-name>.workers.dev`.
   Use it in the callback URL from step 1.

## 3. Point the editor at the helper

In `src/admin/config.yml`, replace
`https://REPLACE-WITH-SIGN-IN-HELPER-URL` with the helper address from step 2,
then commit the change. The site rebuilds automatically.

## 4. Let the site publish itself

1. Run `firebase login:ci` in a terminal and copy the token it prints.
2. On GitHub, open the repository, then **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it `FIREBASE_TOKEN` and paste the token.

## 5. Give the client access

1. On GitHub, open the repository, then **Settings → Collaborators → Add people**.
2. Add the client's GitHub username with **Write** access.
3. The client accepts the invitation by email, then can sign in at `/admin`.

## Testing

1. Open `https://alirsabah.web.app/admin` and click **Login with GitHub**.
2. Make a small change (for example, edit one team member's role) and click **Publish**.
3. Within a few minutes, the change should appear on the live site.
   Check the **Actions** tab on GitHub if it does not.
