const BACKEND_BASE_URL =
  import.meta?.env?.VITE_BACKEND_URL || "/api";

async function httpPost(path, payload) {
  const response = await fetch(`${BACKEND_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Backend error (${response.status}): ${errorText || response.statusText}`
    );
  }

  return response.json();
}

export async function sendChatMessage(query) {
  return httpPost("/chat", { query });
}
