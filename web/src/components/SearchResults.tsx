import React, { useEffect, useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchSearch, type Response } from '../queries/searchQuery'

const SearchResults: React.FC<{ query: { location: string | null; energyRating?: string }; searchTrigger: number }> = ({ query, searchTrigger }) => {
	const [pageIndex, setPageIndex] = useState(0);
	const PAGE_SIZE = 20;

	// Reset pagination when searchTrigger changes (new search initiated)
	useEffect(() => {
		setPageIndex(0);
	}, [searchTrigger]);


	const hasText = !!query.location && String(query.location).trim().length > 0;
	const { isPending, isError, error, data, isFetching } = useQuery<Response, Error>({
		queryKey: ['search', query, pageIndex, searchTrigger],
		queryFn: () => fetchSearch({query, pageIndex, pageSize: PAGE_SIZE}),
		enabled: hasText,
		placeholderData: keepPreviousData,
	});


	if (!hasText) return <div>Enter a postcode to search.</div>
	if (isPending || (isFetching && !data)) return <div>Searching...</div>
	if (isError) return <div>Error: {error.message}</div>

	const { results, total, took, offset, limit } = data ?? {results: []}
	const nextPageExists = (offset ?? 0) + (limit ?? 0) < (total ?? 0);

	return (
		<div>
			{results.length > 0 ? (
				<>
				<table>
					<thead>
						<tr>
							<th>Address</th>
							<th>EPC Rating</th>					
							<th>Running Cost</th>
						</tr>
					</thead>
					<tbody>
						{results.map((res) => (
							<tr key={res.uprn}>
								<td>{res.address}</td>
								<td>{res["current_energy_rating"] ?? "unknown"}</td>
								<td>{String(res["running_cost"] ?? "unknown")}</td>
							</tr>
						))}
					</tbody>
				</table>
				

				<ul style={{ listStyle: 'none', padding: 0, display: 'flex', gap: '16px', marginTop: '16px' }}>
					<li>Total results: {total}</li>
					<li>Offset: {offset}</li>
					<li>Limit: {limit}</li>
					<li>Search took: {took} ms</li>
				</ul>
					

				Current page: {pageIndex + 1} of {Math.ceil((total ?? 0) / (limit ?? 10))}
				<button onClick={() => setPageIndex((p) => Math.max(0, p - 1))} disabled={pageIndex === 0}>Previous</button>
				<button onClick={() => setPageIndex((p) => p + 1)} disabled={!nextPageExists}>Next</button>

				</>
			) : (
				<div>No results</div>
			)}

		</div>
	)
}

export default SearchResults
