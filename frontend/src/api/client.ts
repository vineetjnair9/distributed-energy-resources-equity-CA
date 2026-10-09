import type { components } from "./schema";

// Generated from docs/openapi.json (npm run gen:types); never edit by hand.
type Schemas = components["schemas"];
export type Health = Schemas["HealthResponse"];
export type Region = Schemas["Region"];
export type RegionList = Schemas["RegionList"];
export type RegionDetail = Schemas["RegionDetail"];
export type Metric = Schemas["Metric"];
export type ModelOutput = Schemas["ModelOutput"];
export type ModelOutputList = Schemas["ModelOutputList"];
export type Evidence = Schemas["Evidence"];
export type CompareResponse = Schemas["CompareResponse"];
export type SummaryResponse = Schemas["SummaryResponse"];
export type SummaryCategoryList = Schemas["SummaryCategoryList"];
export type Facets = Schemas["Facets"];
export type ScreeningResponse = Schemas["ScreeningResponse"];

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? `Request failed (${response.status})`;
    throw new ApiError(response.status, message);
  }
  return body as T;
}

export interface RegionQuery {
  q?: string;
  county?: string;
  utility?: string;
  limit?: number;
  offset?: number;
}

function query(params: Record<string, string | number | string[] | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    for (const item of Array.isArray(value) ? value : [value]) search.append(key, String(item));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  health: () => request<Health>("/api/health"),
  regions: (params: RegionQuery = {}) => request<RegionList>(`/api/regions${query({ ...params })}`),
  region: (id: string) => request<RegionDetail>(`/api/regions/${encodeURIComponent(id)}`),
  modelOutput: (id: string) => request<ModelOutputList>(`/api/model-output/${encodeURIComponent(id)}`),
  summaries: (id: string) => request<SummaryCategoryList>(`/api/regions/${encodeURIComponent(id)}/summaries`),
  summaryCategories: () => request<Record<string, string>>("/api/summary-categories"),
  summary: (region_id: string, category: string) =>
    request<SummaryResponse>("/api/summaries", {
      method: "POST",
      body: JSON.stringify({ region_id, category }),
    }),
  facets: () => request<Facets>("/api/facets"),
  screening: (params: { outcome_name: string; county?: string; utility?: string; limit?: number }) =>
    request<ScreeningResponse>(`/api/screening${query({ ...params })}`),
  compare: (ids: string[]) => request<CompareResponse>(`/api/compare${query({ region_ids: ids })}`),
};
