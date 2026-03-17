// Utility to map raw pipeline events (e.g. SSE or HTTP responses)
// into a normalized structure for the UI.
// TODO: adapt when the real backend contract is defined.

export function mapPipelineEvents(events = []) {
  // For now, just return a trivial structure.
  return {
    steps: events.map((e, index) => ({
      id: e.id ?? index,
      status: e.status ?? "info",
      message: e.message ?? "",
      agent: e.agent ?? null,
      detail: e.detail ?? {},
    })),
  };
}

export default mapPipelineEvents;

