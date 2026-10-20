import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <main className="page-shell">
      <section className="section-card">
        <p className="section-badge">404</p>
        <h1>Страница не найдена</h1>
        <p>Проверьте адрес или вернитесь на главную страницу.</p>
        <Link to="/" className="button button-primary">
          На главную
        </Link>
      </section>
    </main>
  );
}