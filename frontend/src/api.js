// The browser only ever calls relative /api/... URLs. Vite (dev), nginx (compose)
// and the Ingress (Kubernetes) route them to the backend.
const API = '/api/items';

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join(', ');
    } catch {
      // not JSON - keep the status text
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export function listItems(filters) {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
  return request(`${API}?${params}`);
}

export const getStats = () => request(`${API}/stats`);
export const createItem = (item) => request(API, { method: 'POST', body: JSON.stringify(item) });
export const updateItem = (id, changes) => request(`${API}/${id}`, { method: 'PUT', body: JSON.stringify(changes) });
export const resolveItem = (id) => request(`${API}/${id}/resolve`, { method: 'POST' });
export const deleteItem = (id) => request(`${API}/${id}`, { method: 'DELETE' });
