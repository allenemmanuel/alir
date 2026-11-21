// Sign-in helper for the website editor (/admin).
//
// The editor needs a small service to finish "Sign in with GitHub".
// This file is that service. It runs on Cloudflare Workers (free tier).
// Setup steps are in SETUP.md. Nothing here needs to be edited by the client.
//
// Required settings (set in Cloudflare, never written in this file):
//   GITHUB_CLIENT_ID      from the GitHub OAuth app
//   GITHUB_CLIENT_SECRET  from the GitHub OAuth app (keep secret)
//   SITE_ORIGIN           the website address, e.g. https://alirsabah.web.app

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/auth") return startSignIn(url, env);
    if (url.pathname === "/callback") return finishSignIn(url, env);
    return new Response("Not found", { status: 404 });
  },
};

// Step 1: send the editor's sign-in window to GitHub.
function startSignIn(url, env) {
  const github = new URL("https://github.com/login/oauth/authorize");
  github.searchParams.set("client_id", env.GITHUB_CLIENT_ID);
  github.searchParams.set("redirect_uri", `${url.origin}/callback`);
  github.searchParams.set("scope", "repo");
  return Response.redirect(github.toString(), 302);
}

// Step 2: GitHub sends the person back here with a code. Trade it for a token.
async function finishSignIn(url, env) {
  const code = url.searchParams.get("code");
  if (!code) return page("Sign-in was cancelled or failed. Please close this window and try again.", null, env);

  const response = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });
  const data = await response.json();
  if (!data.access_token) return page("GitHub did not accept the sign-in. Please try again.", null, env);
  return page("Signed in. You can close this window.", data.access_token, env);
}

// Hands the result back to the editor window, which only accepts messages from the website.
function page(message, token, env) {
  const origin = JSON.stringify(env.SITE_ORIGIN);
  const script = token
    ? `
      (function () {
        var token = ${JSON.stringify(token)};
        function receive(e) {
          if (e.origin !== ${origin}) return;
          window.removeEventListener("message", receive, false);
          window.opener.postMessage(
            "authorization:github:success:" + JSON.stringify({ token: token, provider: "github" }),
            e.origin
          );
        }
        window.addEventListener("message", receive, false);
        window.opener.postMessage("authorizing:github", ${origin});
      })();`
    : "";
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>ALIR editor sign-in</title></head>
<body style="font-family:system-ui,sans-serif;padding:2rem;line-height:1.5">
<p>${message.replace(/</g, "&lt;")}</p>
<script>${script}</script>
</body></html>`;
  return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
}
