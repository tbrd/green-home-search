// Fields commonly returned by the EPC `/domestic/search` endpoint.
// The OpenAPI `Certificate` schema is an object without explicit
// properties, so keep fields optional and permissive.
export interface Result {
	// Identifiers
	uprn: string;

	// Address/display
	name?: string;
	address: string;
	address_line?: string;
	postcode?: string;

	// Coordinates (some providers use latitude/longitude)
	lat?: number;
	lng?: number;
	latitude?: number;
	longitude?: number;

	// Misc
	distance_m?: number;
	current_energy_rating?: string;
	energy_rating?: string;

	running_cost?: number;

	// allow other fields
	[key: string]: unknown;
}

export const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

export type Response = {
	results: Result[];
	total?: number;
	took?: number;
	offset?: number;
	limit?: number;
}



export const fetchSearch = async ({query: q, pageIndex = 0, pageSize = 10}: {query: {location: string | null, energyRating?: string}, pageIndex: number, pageSize?: number }): Promise<Response> => {
	if (!q.location) return { results: [] };

	const searchParams = new URLSearchParams();

	searchParams.set('address', q.location);
	if (q.energyRating) {
		searchParams.set('energy_rating', q.energyRating);
	}
	searchParams.set('offset', (pageIndex * pageSize).toString());
	searchParams.set('limit', pageSize.toString());

	const url = `${API_BASE}/search?${searchParams.toString()}`;
	const res = await fetch(url);

	// Treat 404 as an error so the UI surfaces it explicitly
	if (res.status === 404) {
		const text = await res.text().catch(() => '');
		throw new Error(`HTTP 404 Not Found${text ? ' - ' + text : ''}`);
	}

	if (!res.ok) {
		const text = await res.text().catch(() => '');
		throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ' - ' + text : ''}`);
	}

	const text = await res.text().catch(() => '');

	let payload: Response;
	try {
		payload = text ? JSON.parse(text) as Response : { results: [] };
	} catch {
		throw new Error(`Invalid JSON response`);
	}

	return payload;
}
