import { useEffect, useMemo, useRef, useState } from 'react';
import { MetricsClient } from '../api/metricsClient';

/**
 * PUBLIC_INTERFACE
 * Poll current metrics via HTTP (WebSockets later).
 *
 * - Uses conditional requests (ETag / Last-Modified) when provided by backend.
 * - Aborts in-flight requests when toggles change or component unmounts.
 *
 * @param {Object} params
 * @param {number} [params.pollIntervalMs=1000]
 * @param {boolean} [params.includePerStream=false]
 * @returns {{
 *  metrics: any,
 *  loading: boolean,
 *  error: string | null,
 *  lastUpdatedAt: number | null,
 *  etag: string | null,
 *  lastModified: string | null
 * }}
 */
export function useCurrentMetrics({ pollIntervalMs = 1000, includePerStream = false } = {}) {
  const client = useMemo(() => new MetricsClient(), []);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [etag, setEtag] = useState(null);
  const [lastModified, setLastModified] = useState(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null);

  const timerRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    async function pollOnce() {
      // Cancel previous request if still running.
      if (abortRef.current) abortRef.current.abort();
      const abortController = new AbortController();
      abortRef.current = abortController;

      try {
        const result = await client.fetchCurrentMetrics({
          includePerStream,
          etag,
          lastModified,
          signal: abortController.signal,
        });

        if (!isMounted) return;

        if (!result.notModified && result.metrics) {
          setMetrics(result.metrics);
          setLastUpdatedAt(Date.now());
        }
        if (result.etag) setEtag(result.etag);
        if (result.lastModified) setLastModified(result.lastModified);

        setError(null);
        setLoading(false);
      } catch (e) {
        if (!isMounted) return;
        // Ignore abort errors as they are expected when toggles change/unmounting.
        if (e && typeof e === 'object' && e.name === 'AbortError') return;

        setError(e?.message || 'Failed to fetch metrics');
        setLoading(false);
      }
    }

    // Immediately fetch, then schedule interval.
    pollOnce();
    timerRef.current = window.setInterval(pollOnce, Math.max(250, pollIntervalMs));

    return () => {
      isMounted = false;
      if (timerRef.current) window.clearInterval(timerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
    // Intentionally include etag/lastModified so conditional headers evolve correctly.
  }, [client, pollIntervalMs, includePerStream, etag, lastModified]);

  return { metrics, loading, error, lastUpdatedAt, etag, lastModified };
}
