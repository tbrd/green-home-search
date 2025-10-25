// Query helper for the active listings search endpoint (/listings/search)

export interface ListingResult {
  // core identifiers
  id?: string;
  listing_id?: string;
  property_id?: string;

  // listing-specific
  status?: string;
  is_active?: boolean;
  listed_at?: string;
  expires_at?: string;
  price?: number;
  currency?: string;
  bedrooms?: number;
  bathrooms?: number;
  tenure?: string;

  // presentation/links
  url?: string;
  media_urls?: string[];

  // location/display
  address_line?: string;
  postcode?: string;
  location?: { lat: number; lon: number } | string;

  // denormalized EPC attributes
  main_fuel?: string;
  solar_panels?: boolean;
  solar_water_heating?: boolean;
  epc_rating?: string;
  epc_score?: number;
  running_cost_annual?: number;
  running_cost_monthly?: number;

  // allow other fields
  [key: string]: unknown;
}

export const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

export type ListingsResponse = {
  results: ListingResult[];
  total?: number;
  took?: number;
  offset?: number;
  limit?: number;
}

export type ListingsQuery = {
  // text or geo
  q?: string | null;
  lat?: number | null;
  lon?: number | null;
  radiusKm?: number | null; // defaults to 10 on API

  // filters
  bedroomsMin?: number | null;
  mainFuel?: string[] | null;
  solarPanels?: boolean | null;
  solarWaterHeating?: boolean | null;
  runningCostMonthlyMax?: number | null;

  // behavior
  collapsePerProperty?: boolean | null; // defaults true on API
}

export const fetchActiveListings = async ({ query, pageIndex = 0, pageSize = 20 }: { query: ListingsQuery, pageIndex?: number, pageSize?: number }): Promise<ListingsResponse> => {
  const searchParams = new URLSearchParams();

  // paging
  searchParams.set('offset', String(pageIndex * pageSize));
  searchParams.set('size', String(pageSize));

  // query modes
  if (query.q) searchParams.set('q', String(query.q));
  if (query.lat != null && query.lon != null) {
    searchParams.set('lat', String(query.lat));
    searchParams.set('lon', String(query.lon));
    if (query.radiusKm != null) searchParams.set('radius_km', String(query.radiusKm));
  }

  // filters
  if (query.bedroomsMin != null) searchParams.set('bedrooms_min', String(query.bedroomsMin));
  if (query.mainFuel && query.mainFuel.length) {
    for (const f of query.mainFuel) searchParams.append('main_fuel', f);
  }
  if (query.solarPanels != null) searchParams.set('solar_panels', String(query.solarPanels));
  if (query.solarWaterHeating != null) searchParams.set('solar_water_heating', String(query.solarWaterHeating));
  if (query.runningCostMonthlyMax != null) searchParams.set('running_cost_monthly_max', String(query.runningCostMonthlyMax));

  // behavior
  if (query.collapsePerProperty != null) searchParams.set('collapse_per_property', String(query.collapsePerProperty));

  const url = `${API_BASE}/listings/search?${searchParams.toString()}`;
  const res = await fetch(url);

  if (res.status === 404) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP 404 Not Found${text ? ' - ' + text : ''}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ' - ' + text : ''}`);
  }

  const text = await res.text().catch(() => '');

  let payload: ListingsResponse;
  try {
    payload = text ? JSON.parse(text) as ListingsResponse : { results: [] };
  } catch {
    throw new Error('Invalid JSON response');
  }

  // Ensure results always present
  payload.results = payload.results || [];
  return payload;
}
