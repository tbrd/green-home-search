import React, { useEffect, useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { fetchActiveListings, type ListingsResponse, type ListingsQuery } from '../queries/listingsQuery';

type Props = {
  query: ListingsQuery;
  searchTrigger: number; // bump to force new search
  pageSize?: number;
};

const ListingsResults: React.FC<Props> = ({ query, searchTrigger, pageSize = 20 }) => {
  const [pageIndex, setPageIndex] = useState(0);

  // Reset pagination when new search is triggered
  useEffect(() => {
    setPageIndex(0);
  }, [searchTrigger]);

  const { isLoading, error, data } = useQuery<ListingsResponse, Error>({
    queryKey: ['listings', query, pageIndex, searchTrigger],
    queryFn: () => fetchActiveListings({ query, pageIndex, pageSize }),
    enabled: !!query,
    placeholderData: keepPreviousData,
  });

  // A minimal guard: show prompt when neither q nor lat/lon provided
  const hasText = !!query?.q && String(query.q).trim().length > 0;
  const hasGeo = query?.lat != null && query?.lon != null;
  if (!hasText && !hasGeo) {
    return <div>Enter a postcode or provide a map location to search listings.</div>;
  }

  if (isLoading) return <div>Searching listings...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const { results, total, took, offset, limit } = data ?? { results: [] };
  const nextPageExists = (offset ?? 0) + (limit ?? 0) < (total ?? 0);

  return (
    <div>
      {results.length > 0 ? (
        <>
          <table>
            <thead>
              <tr>
                <th>Address</th>
                <th>Price</th>
                <th>Beds</th>
                <th>EPC</th>
                <th>Monthly cost</th>
                <th>Fuel</th>
                <th>Solar</th>
              </tr>
            </thead>
            <tbody>
              {results.map((res, i) => (
                <tr key={(res.id as string) || `${res.property_id}:${res.listing_id}:${i}`}>
                  <td>{res.address_line || res.postcode || '(unknown)'}</td>
                  <td>{res.price != null ? `£${res.price.toLocaleString()}` : '—'}</td>
                  <td>{res.bedrooms ?? '—'}</td>
                  <td>{res.epc_rating ?? '—'}</td>
                  <td>{res.running_cost_monthly != null ? `£${res.running_cost_monthly}` : '—'}</td>
                  <td>{res.main_fuel ?? '—'}</td>
                  <td>
                    {res.solar_panels ? 'PV' : ''}
                    {res.solar_water_heating ? (res.solar_panels ? ' + ' : '') + 'Solar HW' : ''}
                    {!res.solar_panels && !res.solar_water_heating ? '—' : ''}
                  </td>
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

          <div style={{ marginTop: 8 }}>
            Current page: {pageIndex + 1} of {Math.ceil((total ?? 0) / (limit ?? pageSize))}
          </div>
          <button onClick={() => setPageIndex((p) => Math.max(0, p - 1))} disabled={pageIndex === 0}>
            Previous
          </button>
          <button onClick={() => setPageIndex((p) => p + 1)} disabled={!nextPageExists}>
            Next
          </button>
        </>
      ) : (
        <div>No listings found</div>
      )}
    </div>
  );
};

export default ListingsResults;
