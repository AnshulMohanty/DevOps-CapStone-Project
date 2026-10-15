import { useCallback, useEffect, useState } from 'react';
import { createItem, deleteItem, getStats, listItems, resolveItem, updateItem } from './api.js';
import StatsCards from './components/StatsCards.jsx';
import Toolbar from './components/Toolbar.jsx';
import ItemCard from './components/ItemCard.jsx';
import ReportModal from './components/ReportModal.jsx';

const EMPTY_STATS = { total: 0, open_lost: 0, open_found: 0, claimed: 0, returned: 0, by_category: {} };

export default function App() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [filters, setFilters] = useState({ type: '', status: '', category: '', q: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showReport, setShowReport] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      const [list, numbers] = await Promise.all([listItems(filters), getStats()]);
      setItems(list);
      setStats(numbers);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Debounce so typing in the search box sends one request, not one per key.
  useEffect(() => {
    const timer = setTimeout(load, filters.q ? 250 : 0);
    return () => clearTimeout(timer);
  }, [load, filters.q]);

  const act = async (id, action) => {
    setBusyId(id);
    try {
      await action();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyId(null);
    }
  };

  const handleCreate = async (item) => {
    await createItem(item); // errors are shown inside the modal
    setShowReport(false);
    await load();
  };

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">🔎</span>
          <div>
            <strong>FoundIt</strong>
            <small>Campus Lost &amp; Found</small>
          </div>
        </div>
        <button className="btn primary" onClick={() => setShowReport(true)}>
          + Report an item
        </button>
      </header>

      <main className="content">
        <section className="hero">
          <h1>Lost something? Found something?</h1>
          <p>Post it here so it finds its way back to its owner.</p>
        </section>

        <StatsCards stats={stats} />

        <Toolbar filters={filters} onChange={setFilters} />

        {error && (
          <div className="alert" role="alert">
            <span>⚠ Could not reach the FoundIt API: {error}</span>
            <button className="btn small" onClick={load}>Retry</button>
          </div>
        )}

        {loading ? (
          <div className="grid">
            {[1, 2, 3].map((n) => <div className="card skeleton" key={n} />)}
          </div>
        ) : error && items.length === 0 ? null : items.length === 0 ? (
          <div className="empty">
            <span className="empty-icon">🧺</span>
            <h3>Nothing here yet</h3>
            <p>
              {Object.values(filters).some(Boolean)
                ? 'No items match these filters. Try clearing them.'
                : 'No items reported so far. Be the first to post one.'}
            </p>
          </div>
        ) : (
          <div className="grid">
            {items.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                busy={busyId === item.id}
                onClaim={() => act(item.id, () => updateItem(item.id, { status: 'CLAIMED' }))}
                onResolve={() => act(item.id, () => resolveItem(item.id))}
                onDelete={() => {
                  if (window.confirm(`Delete "${item.title}"?`)) act(item.id, () => deleteItem(item.id));
                }}
              />
            ))}
          </div>
        )}
      </main>

      <footer className="footer">
        FoundIt v{__APP_VERSION__} · built and shipped with Docker, GitHub Actions, Helm, Argo CD &amp; EKS
      </footer>

      {showReport && <ReportModal onClose={() => setShowReport(false)} onSubmit={handleCreate} />}
    </div>
  );
}
