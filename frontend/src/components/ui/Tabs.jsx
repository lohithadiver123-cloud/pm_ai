import Icon from '../Icon';

/**
 * The one tab pattern.
 *
 * Rendered as a real tablist with aria-selected, so the active tab is exposed
 * to assistive tech rather than only being a different colour. Works as either
 * an uncontrolled visual switch (onChange) or a panel switch.
 */
export function Tabs({ tabs, value, onChange, label, className = '' }) {
  return (
    <div className={['tabs', className].filter(Boolean).join(' ')} role="tablist" aria-label={label}>
      {tabs.map((tab) => {
        const selected = tab.value === value;
        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            id={`tab-${tab.value}`}
            aria-selected={selected}
            aria-controls={tab.panelId}
            tabIndex={selected ? 0 : -1}
            className="tab"
            onClick={() => onChange(tab.value)}
          >
            {tab.icon && <Icon name={tab.icon} size={14} />}
            {tab.label}
            {tab.count != null && <span className="badge-num">{tab.count}</span>}
          </button>
        );
      })}
    </div>
  );
}

export default Tabs;
