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

	// allow other fields
	[key: string]: any;
}

export const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

export async function fetchSearch(q: string | null, searchAfter?: string) {
	if (!q) return { data: [] as Result[] };

	const searchParams = new URLSearchParams();
	
	searchParams.set('address', q);
	if (searchAfter) searchParams.set('searchAfter', searchAfter);

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

	let payload: any = null;
	try {
		payload = text ? JSON.parse(text) : null;
	} catch (e) {
		throw new Error(`Invalid JSON response`);
	}

	const dedupedPayload: Result[] = payload.reduce((acc: Result[], item: Result) => {
		if (!acc.find(i => i.uprn === item.uprn)) {
			acc.push(item);
		}
		return acc;
	}, [] as Result[]);

	return {
		data: dedupedPayload,
		nextSearchAfter: res.headers.get('X-Next-Search-After') ?? undefined
	}
}
