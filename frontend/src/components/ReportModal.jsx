import { useEffect, useState } from 'react';
import { CATEGORIES } from '../constants.js';

export default function ReportModal({ onClose, onSubmit }) {
  const [type, setType] = useState('LOST');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const submit = async (e) => {
    e.preventDefault();
    // Read the form before any await: React may reuse the event afterwards.
    const form = new FormData(e.currentTarget);
    setSaving(true);
    setError('');
    try {
      await onSubmit({
        type,
        title: form.get('title').trim(),
        category: form.get('category'),
        location: form.get('location').trim(),
        description: form.get('description').trim(),
        reported_by: form.get('reported_by').trim(),
        contact: form.get('contact').trim(),
      });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <div className="backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={submit} aria-label="Report an item">
        <div className="modal-head">
          <h2>Report an item</h2>
          <button type="button" className="close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="segmented" role="radiogroup" aria-label="Lost or found">
          {['LOST', 'FOUND'].map((value) => (
            <button
              type="button"
              key={value}
              role="radio"
              aria-checked={type === value}
              className={type === value ? `seg active ${value.toLowerCase()}` : 'seg'}
              onClick={() => setType(value)}
            >
              {value === 'LOST' ? 'I lost something' : 'I found something'}
            </button>
          ))}
        </div>

        <label>
          What is it?
          <input name="title" required maxLength={120} placeholder="e.g. Blue Milton water bottle" autoFocus />
        </label>
        <div className="row">
          <label>
            Category
            <select name="category" defaultValue="OTHER">
              {Object.entries(CATEGORIES).map(([value, { label, icon }]) => (
                <option key={value} value={value}>{icon} {label}</option>
              ))}
            </select>
          </label>
          <label>
            {type === 'LOST' ? 'Where did you lose it?' : 'Where did you find it?'}
            <input name="location" required maxLength={120} placeholder="e.g. Library, 2nd floor" />
          </label>
        </div>
        <label>
          <span>Details <span className="hint">(optional)</span></span>
          <textarea name="description" rows={3} placeholder="Colour, brand, stickers… anything that helps identify it" />
        </label>
        <div className="row">
          <label>
            Your name
            <input name="reported_by" required maxLength={80} />
          </label>
          <label>
            <span>Contact <span className="hint">(optional)</span></span>
            <input name="contact" maxLength={120} placeholder="phone or email" />
          </label>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}

        <button className="btn primary full" disabled={saving}>
          {saving ? 'Posting…' : 'Post to the board'}
        </button>
      </form>
    </div>
  );
}
