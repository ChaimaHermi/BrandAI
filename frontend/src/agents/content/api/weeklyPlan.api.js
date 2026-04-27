const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

async function handleResponse(res) {
  let data = null;
  try {
    data = await res.json();
  } catch {
    if (res.ok) return null;
  }
  if (!res.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : "Une erreur est survenue.");
  }
  return data;
}

export async function apiGenerateWeeklyPlan(token, body) {
  const res = await fetch(`${AI_URL}/content/weekly-plan/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function apiRegenerateWeeklyItem(token, item, feedback) {
  const res = await fetch(`${AI_URL}/content/weekly-plan/regenerate-item`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ item, feedback }),
  });
  return handleResponse(res);
}

export async function apiApproveWeeklyPlan(token, body) {
  const res = await fetch(`${AI_URL}/content/weekly-plan/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function apiGenerateWeeklyPlanContent(token, body) {
  const res = await fetch(`${AI_URL}/content/weekly-plan/generate-content`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}
