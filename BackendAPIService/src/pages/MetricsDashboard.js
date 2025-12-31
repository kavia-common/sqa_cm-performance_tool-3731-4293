import React, { useMemo, useState } from 'react';
import '../App.css';
import { getApiBaseUrlForDisplay } from '../api/metricsClient';
import { useCurrentMetrics } from '../hooks/useCurrentMetrics';

function formatGbps(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--';
  // Keep it wall-readable: 2 decimals, but avoid overly long strings.
  return Number(v).toFixed(2);
}

function formatPct(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--';
  return Number(v).toFixed(3);
}

function formatTs(ts) {
  if (!ts) return '--';
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return String(ts);
  }
}

function renderErrorCounters(errorCounters) {
  const entries = Object.entries(errorCounters || {});
  if (entries.length === 0) {
    return (
      <div className="errors-empty">
        <div className="small-label">Errors</div>
        <div className="muted">No error counters reported</div>
      </div>
    );
  }

  // Sort by highest counter (desc) then name
  entries.sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0) || a[0].localeCompare(b[0]));

  // Keep it compact; show top N, but allow scroll if more.
  return (
    <div className="errors-grid" role="list" aria-label="Error counters">
      {entries.map(([k, v]) => (
        <div key={k} className="error-tile" role="listitem">
          <div className="small-label">{k}</div>
          <div className="error-value">{Number(v).toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
}

// PUBLIC_INTERFACE
function MetricsDashboard() {
  const [showPerStream, setShowPerStream] = useState(false);
  const apiBase = useMemo(() => getApiBaseUrlForDisplay(), []);

  const { metrics, loading, error, lastUpdatedAt, etag, lastModified } = useCurrentMetrics({
    pollIntervalMs: 1000,
    includePerStream: showPerStream,
  });

  const perStream = metrics?.per_stream || [];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="dashboard-title">SQA_CM Performance Dashboard</div>
          <div className="dashboard-subtitle">
            API: <span className="mono">{apiBase}</span>
          </div>
        </div>

        <div className="header-right">
          <label className="toggle">
            <input
              type="checkbox"
              checked={showPerStream}
              onChange={(e) => setShowPerStream(e.target.checked)}
            />
            <span className="toggle-label">Per-stream</span>
          </label>

          <div className="meta">
            <div>
              <span className="small-label">Updated</span>
              <span className="mono">
                {metrics?.ts ? formatTs(metrics.ts) : lastUpdatedAt ? new Date(lastUpdatedAt).toLocaleString() : '--'}
              </span>
            </div>
            <div className="meta-row">
              <span className="small-label">Seq</span>
              <span className="mono">{metrics?.sequence ?? '--'}</span>
            </div>
          </div>
        </div>
      </header>

      {error ? (
        <div className="banner banner-error" role="alert">
          <div className="banner-title">Metrics fetch error</div>
          <div className="banner-body">{error}</div>
          <div className="banner-body muted">
            Check that the FastAPI service is reachable and CORS allows this origin.
          </div>
        </div>
      ) : null}

      {metrics?.compensated ? (
        <div className="banner banner-warn" role="status">
          <div className="banner-title">Compensated snapshot</div>
          <div className="banner-body">
            The backend detected a polling gap and held the last values.
            {metrics?.reason ? <span className="mono"> ({metrics.reason})</span> : null}
          </div>
        </div>
      ) : null}

      <main className="dashboard-main">
        <section className="hero-grid" aria-label="Key metrics">
          <div className="hero-card">
            <div className="hero-label">Rx</div>
            <div className="hero-value">{loading && !metrics ? '--' : formatGbps(metrics?.rx_gbps)}</div>
            <div className="hero-unit">Gbps</div>
          </div>

          <div className="hero-card">
            <div className="hero-label">Tx</div>
            <div className="hero-value">{loading && !metrics ? '--' : formatGbps(metrics?.tx_gbps)}</div>
            <div className="hero-unit">Gbps</div>
          </div>

          <div className="hero-card loss-card">
            <div className="hero-label">Loss</div>
            <div className="hero-value">{loading && !metrics ? '--' : formatPct(metrics?.loss_pct)}</div>
            <div className="hero-unit">%</div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div className="panel-title">Error Counters</div>
            <div className="panel-meta mono">
              {etag ? `ETag: ${etag}` : 'ETag: --'} &nbsp;|&nbsp; {lastModified ? `Last-Modified: ${lastModified}` : 'Last-Modified: --'}
            </div>
          </div>
          {renderErrorCounters(metrics?.error_counters)}
        </section>

        {showPerStream ? (
          <section className="panel">
            <div className="panel-header">
              <div className="panel-title">Per-stream</div>
              <div className="panel-meta">{Array.isArray(perStream) ? `${perStream.length} streams` : '0 streams'}</div>
            </div>

            {Array.isArray(perStream) && perStream.length > 0 ? (
              <div className="table-wrap" role="region" aria-label="Per-stream metrics table">
                <table className="stream-table">
                  <thead>
                    <tr>
                      <th align="left">Stream</th>
                      <th align="right">Rx (Gbps)</th>
                      <th align="right">Tx (Gbps)</th>
                      <th align="right">Frame (B)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {perStream.map((s) => (
                      <tr key={s.stream_id}>
                        <td className="mono">{s.stream_id}</td>
                        <td align="right" className="mono">{formatGbps(s.rx_gbps)}</td>
                        <td align="right" className="mono">{formatGbps(s.tx_gbps)}</td>
                        <td align="right" className="mono">{Number(s.frame_size).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="muted">No per-stream data (enable streams on backend or wait for first samples).</div>
            )}
          </section>
        ) : null}
      </main>

      <footer className="dashboard-footer">
        <div className="muted">
          HTTP polling at 1s. WebSockets will be added later.
        </div>
      </footer>
    </div>
  );
}

export default MetricsDashboard;
