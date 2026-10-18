import { useId, type ReactNode } from 'react';

type AccordionProps = {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
  className: string;
};

export function Accordion({ title, open, onToggle, children, className }: AccordionProps) {
  const panelId = useId();
  const stateClassName = open ? ` ${className}--open` : '';

  return (
    <div className={`${className}-group`}>
      <button
        className={`${className}${stateClassName}`}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={onToggle}
      >
        <span>{title}</span>
        <span className={`accordion-chevron${open ? ' accordion-chevron--open' : ''}`} aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </span>
      </button>
      <div id={panelId} className={`${className}-panel`} hidden={!open}>
        {children}
      </div>
    </div>
  );
}
