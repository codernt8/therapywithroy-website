import type { Context, Config } from "@netlify/edge-functions";

export default async (request: Request, context: Context) => {
  const expectedUser = Netlify.env.get("PREVIEW_AUTH_USER");
  const expectedPass = Netlify.env.get("PREVIEW_AUTH_PASS");

  if (!expectedUser || !expectedPass) {
    return context.next();
  }

  const authHeader = request.headers.get("authorization") || "";
  const [scheme, encoded] = authHeader.split(" ");

  if (scheme === "Basic" && encoded) {
    try {
      const decoded = atob(encoded);
      const separatorIndex = decoded.indexOf(":");
      const suppliedUser = decoded.slice(0, separatorIndex);
      const suppliedPass = decoded.slice(separatorIndex + 1);

      if (suppliedUser === expectedUser && suppliedPass === expectedPass) {
        return context.next();
      }
    } catch {
      // Malformed header, fall through to the auth challenge below.
    }
  }

  return new Response("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Therapy with Roy - Preview", charset="UTF-8"',
      "Content-Type": "text/plain",
    },
  });
};

export const config: Config = {
  path: "/*",
};