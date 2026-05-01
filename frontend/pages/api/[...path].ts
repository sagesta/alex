import type { NextApiRequest, NextApiResponse } from "next";

export const config = {
  api: {
    bodyParser: false,
  },
};

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function getBackendUrl(): string {
  const raw =
    process.env.BACKEND_URL ||
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "";
  return raw.trim().replace(/\/$/, "");
}

async function readBody(req: NextApiRequest): Promise<ArrayBuffer | undefined> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  if (chunks.length === 0) {
    return undefined;
  }
  const buffer = Buffer.concat(chunks);
  const body = new ArrayBuffer(buffer.byteLength);
  new Uint8Array(body).set(buffer);
  return body;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    res.status(502).json({
      detail:
        "Frontend API proxy is not configured. Set BACKEND_URL on the frontend service.",
    });
    return;
  }

  const pathAndQuery = req.url?.replace(/^\/api/, "") || "";
  const targetUrl = `${backendUrl}/api${pathAndQuery}`;

  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (HOP_BY_HOP_HEADERS.has(key.toLowerCase()) || value === undefined) {
      continue;
    }
    if (Array.isArray(value)) {
      headers.set(key, value.join(", "));
    } else {
      headers.set(key, value);
    }
  }

  const method = req.method || "GET";
  const body = method === "GET" || method === "HEAD" ? undefined : await readBody(req);

  try {
    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
    });

    response.headers.forEach((value, key) => {
      if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });

    const responseBody = Buffer.from(await response.arrayBuffer());
    res.status(response.status).send(responseBody);
  } catch (error) {
    console.error("API proxy request failed:", error);
    res.status(502).json({ detail: "Unable to reach the portfolio API service." });
  }
}
