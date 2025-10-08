import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import DebugPanel from './DebugPanel'
import { type Result, fetchSearch, API_BASE } from '../queries/searchQuery'

const SearchResults: React.FC<{ query: string | null; }> = ({ query }) => {
	const queryResult = useQuery<Result[], Error>({
		queryKey: ['search', query],
		queryFn: () => fetchSearch(query),
		enabled: !!query,
	})

	const { data, error, isLoading } = queryResult
	const [lastRequestUrl, setLastRequestUrl] = useState<string | undefined>(undefined)
	const [lastRawResponse, setLastRawResponse] = useState<string | undefined>(undefined)

	// set debug info when query finishes
	React.useEffect(() => {
		if (!query) {
			setLastRequestUrl(undefined)
			setLastRawResponse(undefined)
			return
		}
		const url = `${API_BASE}/search?address=${encodeURIComponent(query)}`
		setLastRequestUrl(url)
		// try to store raw response when available
		if (data) setLastRawResponse(JSON.stringify(data, null, 2))
		if (error) setLastRawResponse((error as Error).message)
	}, [query, data, error])

	if (!query) return <div>Enter a location to search.</div>
	if (isLoading) return <div>Searching...</div>
	if (error) return <div>Error: {error.message}</div>

	const results = data ?? []

	return (
		<div>
			<h2>Results for “{query}”</h2>
			{results.length > 0 ? (
				<ul>
					{results.map((res) => {
						
						return (
							<li key={res.uprn} style={{ marginBottom: 8 }}>
								<strong>{res.address}</strong>
								<div style={{ fontSize: 12 }}>{res["built-form"] ?? "unknown"}</div>
								<div style={{ fontSize: 12 }}>Energy rating: {res["current-energy-rating"] ?? "unknown"}</div>
							</li>
						)
					})}
				</ul>
			) : (
				<div>No results</div>
			)}

			<DebugPanel requestUrl={lastRequestUrl} rawResponse={lastRawResponse} error={error ? (error as Error).message : undefined} />
		</div>
	)
}

export default SearchResults
