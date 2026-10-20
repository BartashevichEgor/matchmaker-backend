import { useState } from 'react';
import { useLocation, Link, Outlet, type Location as RouterLocation } from 'react-router-dom';
import { useAuth } from '../../app/providers/AuthProvider';

type NavItem = {
  path: string;
  label: string;
  displayLabel: string;
  icon: SidebarIconName;
  exact?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { path: '/feed', label: 'Feed', displayLabel: 'Каталог', icon: 'feed', exact: true },
  { path: '/matches', label: 'Matches', displayLabel: 'Мэтчи', icon: 'matches', exact: true },
  { path: '/profile', label: 'Profile', displayLabel: 'Профиль', icon: 'profile' },
];

const MOBILE_NAV_ITEMS: NavItem[] = [
  ...NAV_ITEMS,
];

type SidebarIconName = 'feed' | 'projects' | 'profile' | 'matches' | 'logout' | 'menu';

function SidebarIcon({ name }: { name: SidebarIconName }) {
  const commonProps = {
    className: 'sidebar-icon',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: '1.8',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };

  switch (name) {
    case 'feed':
      return (
        <svg {...commonProps}>
          <path d="M5 4.75h14a1.25 1.25 0 0 1 1.25 1.25v12A1.25 1.25 0 0 1 19 19.25H5A1.25 1.25 0 0 1 3.75 18V6A1.25 1.25 0 0 1 5 4.75Z" />
          <path d="M7.5 9h9M7.5 12h9M7.5 15h5" />
        </svg>
      );
    case 'projects':
      return (
        <svg {...commonProps}>
          <path d="M4.5 6.75A1.75 1.75 0 0 1 6.25 5h4l1.5 1.75h6A1.75 1.75 0 0 1 19.5 8.5v8.75A1.75 1.75 0 0 1 17.75 19h-11A1.75 1.75 0 0 1 5 17.25l-.5-10.5Z" />
          <path d="M5 9h14" />
        </svg>
      );
    case 'profile':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="8" r="3.25" />
          <path d="M5.25 19a6.75 6.75 0 0 1 13.5 0" />
        </svg>
      );
    case 'matches':
      return (
        <svg {...commonProps}>
          <path d="M20.25 8.5c0 5.25-8.25 10-8.25 10S3.75 13.75 3.75 8.5A4.25 4.25 0 0 1 12 6.8a4.25 4.25 0 0 1 8.25 1.7Z" />
        </svg>
      );
    case 'logout':
      return (
        <svg {...commonProps}>
          <path d="M10 5H6.75A1.75 1.75 0 0 0 5 6.75v10.5A1.75 1.75 0 0 0 6.75 19H10" />
          <path d="M14 8l4 4-4 4M18 12H9" />
        </svg>
      );
    case 'menu':
      return (
        <svg {...commonProps}>
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      );
  }
}

function isActive(location: RouterLocation, path: string, exact?: boolean): boolean {
  if (exact) {
    return location.pathname === path;
  }
  return location.pathname.startsWith(path);
}

export function AppLayout() {
  const { logout, authError } = useAuth();
  const location = useLocation();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const handleLogout = async () => {
    if (isLoggingOut) {
      return;
    }

    setLogoutError(null);
    setIsLoggingOut(true);

    try {
      await logout();
    } catch {
      setLogoutError('Не удалось выйти из аккаунта. Попробуйте ещё раз.');
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <div className="app-layout">
      {isMobileMenuOpen ? (
        <button
          className="app-sidebar__backdrop"
          type="button"
          aria-label="Закрыть боковое меню"
          onClick={closeMobileMenu}
        />
      ) : null}

      <aside
        className={`app-sidebar${isMobileMenuOpen ? ' app-sidebar--open' : ''}`}
        aria-label="Боковая навигация"
      >
        <div className="app-sidebar__brand-story" aria-hidden="true">
          <img src="/assets/matchmaker-logo.png" alt="" />
          <strong>Matchmaker</strong>
          <span>Команда начинается с мэтча</span>
        </div>
        <p className="app-sidebar__footer-copy">Люди, навыки и проекты<br />в одном месте</p>

        <nav className="app-sidebar__nav" aria-label="Основная навигация">
          <ul className="app-sidebar__nav-list">
            {NAV_ITEMS.map((item) => (
              <li key={item.path} className="app-sidebar__nav-item">
                <Link
                  to={item.path}
                  className={`app-sidebar__link${isActive(location, item.path, item.exact) ? ' app-sidebar__link--active' : ''}`}
                  title={item.label}
                  aria-label={item.label}
                  aria-current={isActive(location, item.path, item.exact) ? 'page' : undefined}
                  onClick={closeMobileMenu}
                >
                  <SidebarIcon name={item.icon} />
                  <span className="app-sidebar__label">{item.displayLabel}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="app-sidebar__footer">
          <button
            className="app-sidebar__logout"
            type="button"
            onClick={() => void handleLogout()}
            disabled={isLoggingOut}
            aria-busy={isLoggingOut}
            title="Выйти"
            onClickCapture={closeMobileMenu}
          >
            <SidebarIcon name="logout" />
            <span className="app-sidebar__label">{isLoggingOut ? 'Выход...' : 'Выйти'}</span>
          </button>
        </div>
      </aside>

      <nav className="mobile-bottom-nav" aria-label="Мобильная навигация">
        <button
          className="mobile-bottom-nav__item"
          type="button"
          aria-label={isMobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={isMobileMenuOpen}
          onClick={() => setIsMobileMenuOpen((isOpen) => !isOpen)}
        >
          <SidebarIcon name="menu" />
          <span>Menu</span>
        </button>
        {MOBILE_NAV_ITEMS.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`mobile-bottom-nav__item${isActive(location, item.path, item.exact) ? ' mobile-bottom-nav__item--active' : ''}`}
            aria-current={isActive(location, item.path, item.exact) ? 'page' : undefined}
            onClick={closeMobileMenu}
          >
            <SidebarIcon name={item.icon} />
            <span>{item.displayLabel}</span>
          </Link>
        ))}
      </nav>

      <main className="app-content">
        <header className="app-header">
          <Link to="/feed" className="app-header__brand" aria-label="Matchmaker" onClick={closeMobileMenu}>
            <img src="/assets/matchmaker-logo.png" alt="" />
            <span>Matchmaker</span>
          </Link>
          <nav className="app-header__nav" aria-label="Навигация по разделам">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`app-header__link${isActive(location, item.path, item.exact) ? ' app-header__link--active' : ''}`}
                aria-label={item.label}
                aria-current={isActive(location, item.path, item.exact) ? 'page' : undefined}
              >
                {item.displayLabel}
              </Link>
            ))}
          </nav>
        </header>
        {logoutError || authError ? (
          <p className="auth-form__form-error app-content__error" role="alert">
            {logoutError ?? authError}
          </p>
        ) : null}
        <div className="app-page">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
