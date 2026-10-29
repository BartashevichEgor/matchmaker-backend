import type { ReactNode } from 'react';

type AuthPageLayoutProps = {
  children: ReactNode;
};

export function AuthPageLayout({ children }: AuthPageLayoutProps) {
  return (
    <main className="auth-page-layout">
      <section className="auth-page-layout__visual" aria-label="Презентационная панель">
        <div className="auth-page-layout__visual-art" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="auth-page-layout__visual-content">
          <h1>Matchmaker</h1>
          <p>Команда начинается с мэтча</p>
        </div>
      </section>

      <section className="auth-page-layout__form">
        <div className="section-card auth-page">{children}</div>
      </section>
    </main>
  );
}
