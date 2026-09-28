import type { Context, Config } from "@netlify/edge-functions";

// Gates this preview deploy (staging / drafts) behind "Sign in with Google",
// restricted to the email address(es) listed in ALLOWED_EMAILS.
//
// Required environment variables (Netlify > Site configuration > Environment
// variables, "All scopes"):
//   GOOGLE_CLIENT_ID     - OAuth client ID from Google Cloud Console
//   GOOGLE_CLIENT_SECRET - OAuth client secret (mark "Contains secret values")
//   ALLOWED_EMAILS       - comma-separated list of emails allowed in
//   SESSION_SECRET        - a long random string used to sign session cookies
//
// Fails open (no gate at all) if any of these aren't set, so a partial setup
// never locks anyone out by accident.

const SESSION_COOKIE = "gauth_session";
const STATE_COOKIE = "gauth_state";
const RETURN_COOKIE = "gauth_return";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 90; // 90 days

export default async (request: Request, context: Context) => {
  const clientId = Netlify.env.get("GOOGLE_CLIENT_ID");
  const clientSecret = Netlify.env.get("GOOGLE_CLIENT_SECRET");
  const sessionSecret = Netlify.env.get("SESSION_SECRET");
  const allowedEmails = (Netlify.env.get("ALLOWED_EMAILS") || "")
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);

  if (!clientId || !clientSecret || !sessionSecret || allowedEmails.length === 0) {
    return context.next();
  }

  const url = new URL(request.url);
  const cookies = parseCookies(request.headers.get("cookie") || "");

  if (url.pathname === "/auth/callback") {
    return handleCallback(url, cookies, { clientId, clientSecret, sessionSecret, allowedEmails });
  }

  const session = await verifySession(cookies[SESSION_COOKIE], sessionSecret);
  if (session && allowedEmails.includes(session.email.toLowerCase())) {
    return context.next();
  }

  return redirectToGoogle(url, clientId);
};

export const config: Config = {
  path: "/*",
};

// ---------- OAuth handshake ----------

function redirectToGoogle(url: URL, clientId: string): Response {
  const state = randomToken();
  const redirectUri = `${url.origin}/auth/callback`;

  const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  authUrl.searchParams.set("client_id", clientId);
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("scope", "openid email");
  authUrl.searchParams.set("state", state);

  const headers = new Headers({ Location: authUrl.toString() });
  appendCookie(headers, STATE_COOKIE, state, 300);
  appendCookie(headers, RETURN_COOKIE, url.pathname + url.search, 300);

  return new Response(null, { status: 302, headers });
}

async function handleCallback(
  url: URL,
  cookies: Record<string, string>,
  cfg: { clientId: string; clientSecret: string; sessionSecret: string; allowedEmails: string[] },
): Promise<Response> {
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");

  if (!code || !state || state !== cookies[STATE_COOKIE]) {
    return new Response("Sign-in failed (invalid or expired state). Please try again.", { status: 400 });
  }

  const redirectUri = `${url.origin}/auth/callback`;

  const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: cfg.clientId,
      client_secret: cfg.clientSecret,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
    }),
  });

  if (!tokenResponse.ok) {
    return new Response("Sign-in failed while contacting Google. Please try again.", { status: 502 });
  }

  const tokenData = await tokenResponse.json();
  const idToken = tokenData.id_token as string | undefined;
  if (!idToken) {
    return new Response("Sign-in failed (no ID token returned). Please try again.", { status: 502 });
  }

  const payload = decodeJwtPayload(idToken);
  const email = (payload.email as string | undefined)?.toLowerCase();
  const emailVerified = payload.email_verified === true || payload.email_verified === "true";
  const audienceOk = payload.aud === cfg.clientId;

  if (!email || !emailVerified || !audienceOk) {
    return new Response("Sign-in failed (could not verify your Google account).", { status: 403 });
  }

  if (!cfg.allowedEmails.includes(email)) {
    return new Response(
      `This preview is restricted. ${email} is not on the allowed list. If this should be allowed, add it to ALLOWED_EMAILS in Netlify.`,
      { status: 403 },
    );
  }

  const sessionCookieValue = await createSessionCookie(email, cfg.sessionSecret);
  const returnTo = cookies[RETURN_COOKIE] || "/";

  const headers = new Headers({ Location: returnTo });
  appendCookie(headers, SESSION_COOKIE, sessionCookieValue, SESSION_MAX_AGE_SECONDS);
  clearCookie(headers, STATE_COOKIE);
  clearCookie(headers, RETURN_COOKIE);

  return new Response(null, { status: 302, headers });
}

// ---------- Session cookie signing ----------

async function createSessionCookie(email: string, secret: string): Promise<string> {
  const expires = Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SECONDS;
  const payload = `${email}|${expires}`;
  const signature = await hmac(payload, secret);
  return `${base64UrlEncode(payload)}.${signature}`;
}

async function verifySession(
  cookieValue: string | undefined,
  secret: string,
): Promise<{ email: string } | null> {
  if (!cookieValue) return null;
  const [encodedPayload, signature] = cookieValue.split(".");
  if (!encodedPayload || !signature) return null;

  let payload: string;
  try {
    payload = base64UrlDecode(encodedPayload);
  } catch {
    return null;
  }

  const expectedSignature = await hmac(payload, secret);
  if (expectedSignature !== signature) return null;

  const [email, expiresStr] = payload.split("|");
  const expires = Number(expiresStr);
  if (!email || !expires || Date.now() / 1000 > expires) return null;

  return { email };
}

async function hmac(message: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return base64UrlEncodeBytes(new Uint8Array(signature));
}

// ---------- Small helpers ----------

function randomToken(): string {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return base64UrlEncodeBytes(bytes);
}

function base64UrlEncode(str: string): string {
  return base64UrlEncodeBytes(new TextEncoder().encode(str));
}

function base64UrlEncodeBytes(bytes: Uint8Array): string {
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(str: string): string {
  const padded = str.replace(/-/g, "+").replace(/_/g, "/").padEnd(str.length + ((4 - (str.length % 4)) % 4), "=");
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

function decodeJwtPayload(jwt: string): Record<string, unknown> {
  const parts = jwt.split(".");
  if (parts.length < 2) return {};
  try {
    return JSON.parse(base64UrlDecode(parts[1]));
  } catch {
    return {};
  }
}

function parseCookies(header: string): Record<string, string> {
  const out: Record<string, string> = {};
  header.split(";").forEach((part) => {
    const [k, ...v] = part.trim().split("=");
    if (k) out[k] = decodeURIComponent(v.join("="));
  });
  return out;
}

function appendCookie(headers: Headers, name: string, value: string, maxAgeSeconds: number) {
  headers.append(
    "Set-Cookie",
    `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}; HttpOnly; Secure; SameSite=Lax`,
  );
}

function clearCookie(headers: Headers, name: string) {
  headers.append("Set-Cookie", `${name}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`);
}
