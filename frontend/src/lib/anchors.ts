/** Stable fragment IDs so any page can link to a definition. */
export const slug = (text: string) =>
  text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

export const termHref = (term: string) => `/definitions#${slug(term)}`;
export const metricHref = (metric: string) => `/definitions#metric-${slug(metric)}`;
export const outcomeHref = (outcome: string) => `/definitions#outcome-${slug(outcome)}`;
