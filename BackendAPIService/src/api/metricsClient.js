//
// Metrics API client for Backend/APIService (/v1)
//
// - Uses REACT_APP_API_BASE or REACT_APP_BACKEND_URL for base URL
// - Supports conditional GET via ETag / Last-Modified
//

/**
 * Resolve the API base URL from environment variables.
 *
 * Priority:
 *  1) REACT_APP_API_BASE
 *  2) REACT_APP_BACKEND_URL
 *  3) "" (relative; useful when frontend is reverse-proxied behind same origin)
 */
function resolveApiBaseUrl() {
  const raw =
    (process.env.REACT_APP_API_BASE && process.env.REACT_APP_API_BASE.trim()) ||
    (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL.trim()) ||
    '';

  // Normalize: strip trailing slashes
  return raw.replace(/\/+$/, '');
}

/**
 * Join base URL and a path segment safely.
 * @param {string} base
 * @param {string} path
 */
function joinUrl(base, path) {
  if (!base) return path; // relative
  if (path.startsWith('/')) return `${base}${path}`;
  return `${base}/${path}`;
}

/**
 * @typedef {Object} CurrentMetrics
 * @property {string} ts
 * @property {number} rx_gbps
 * @property {number} tx_gbps
 * @property {number} loss_pct
 * @property {Object.<string, number>} error_counters
 * @property {Array<{stream_id: string, rx_gbps: number, tx_gbps: number, frame_size: number}> | null | undefined} per_stream
 * @property {number} sequence
 * @property {boolean} [compensated]
 * @property {string | null} [reason]
 */

/**
 * @typedef {Object} EnvelopeOk
 * @property {"ok"} status
 * @property {any} data
 */

/**
 * @typedef {Object} FetchCurrentMetricsResult
 * @property {boolean} notModified
 * @property {CurrentMetrics | null} metrics
 * @property {string | null} etag
 * @property {string | null} lastModified
 */

/**
 * Lightweight API client for metrics endpoints.
 */
export class MetricsClient {
  constructor() {
    this._baseUrl = resolveApiBaseUrl();
  }

  /**
   * PUBLIC_INTERFACE
   * Fetch current metrics snapshot.
   *
   * Uses conditional GET if `etag` and/or `lastModified` is provided.
   *
   * @param {Object} params
   * @param {boolean} [params.includePerStream=false]
   * @param {string | null} [params.etag=null]
   * @param {string | null} [params.lastModified=null]
   * @param {AbortSignal | undefined} [params.signal]
   * @returns {Promise<FetchCurrentMetricsResult>}
   */
  async fetchCurrentMetrics({ includePerStream = false, etag = null, lastModified = null, signal } = {}) {
    const url = joinUrl(this._baseUrl, `/v1/metrics/current?includePerStream=${includePerStream ? 'true' : 'false'}`);

    const headers = {};
    if (etag) headers['If-None-Match'] = etag;
    if (lastModified) headers['If-Modified-Since'] = lastModified;

    const res = await fetch(url, {
      method: 'GET',
      headers,
      signal,
    });

    if (res.status === 304) {
      return {
        notModified: true,
        metrics: null,
        etag: etag || null,
        lastModified: lastModified || null,
      };
    }

    if (!res.ok) {
      // Try to read backend envelope error, but don't fail if it's not JSON.
      let details = '';
      try {
        const payload = await res.json();
        details = payload?.error?.message || JSON.stringify(payload);
      } catch {
        try {
          details = await res.text();
        } catch {
          details = '';
        }
      }
      throw new Error(`Failed to fetch current metrics (${res.status} ${res.statusText})${details ? `: ${details}` : ''}`);
    }

    /** @type {EnvelopeOk} */
    const json = await res.json();
    if (!json || json.status !== 'ok') {
      throw new Error('Unexpected API response (expected EnvelopeOk).');
    }

    const newEtag = res.headers.get('ETag');
    const newLastModified = res.headers.get('Last-Modified');

    return {
      notModified: false,
      metrics: json.data,
      etag: newEtag,
      lastModified: newLastModified,
    };
  }
}

export function getApiBaseUrlForDisplay() {
  return resolveApiBaseUrl() || '(relative)';
}
