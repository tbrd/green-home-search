import React, { useEffect, useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import DebugPanel from './DebugPanel'
import { type Result, fetchSearch, API_BASE } from '../queries/searchQuery'

const SearchResults: React.FC<{ query: string | null }> = ({ query}) => {
	const [pages, setPages] = useState<string[]>(["default"]);
	const [page, setPage] = useState(1);

	const queryResult = useQuery<{ data: Result[], nextSearchAfter?: string }, Error>({
		queryKey: ['search', query, page],
		queryFn: () => fetchSearch(query, pages[page]),
		enabled: !!query,
		placeholderData: keepPreviousData,
	});

	const { data: { data, nextSearchAfter } = {}, error, isLoading } = queryResult
	const [lastRequestUrl, setLastRequestUrl] = useState<string | undefined>(undefined)
	const [lastRawResponse, setLastRawResponse] = useState<string | undefined>(undefined)

	// if we have a nextSearchAfter and we're on the last page, add it to the pages list

	useEffect(() => {
		if (nextSearchAfter && page === pages.length) {
			setPages((p) => [...p, nextSearchAfter]);
		}
	}, [nextSearchAfter, pages])


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
				<>
				<ol>
					{results.map((res) => {
						
						return (
							<li key={res.uprn} style={{ marginBottom: 8 }}>
								<strong>{res.address}</strong>
								{/* <div style={{ fontSize: 12 }}>{res["built-form"] ?? "unknown"}</div> */}
								{/* <div style={{ fontSize: 12 }}>Energy rating: {res["current-energy-rating"] ?? "unknown"}</div> */}
							</li>
						)
					})}
				</ol>


				
				Current page: {page}
				<button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 1}>Previous</button>
				<button onClick={() => setPage((p) => p + 1)} disabled={!pages[page]}>Next</button>

				</>
			) : (
				<div>No results</div>
			)}

			<DebugPanel requestUrl={lastRequestUrl} rawResponse={lastRawResponse} error={error ? (error as Error).message : undefined} />
		</div>
	)
}

export default SearchResults
