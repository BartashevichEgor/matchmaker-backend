import { Link } from 'react-router-dom';

export function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="section-badge">Matchmaker</p>
        <h1>Подбор проектов и людей для совместной работы</h1>
        <p>
          Это стартовая страница MVP. Здесь будут вход, регистрация и переход к основным разделам приложения.
        </p>
        <div className="hero-actions">
          <Link to="/login" className="button button-primary">
            Войти
          </Link>
          <Link to="/register" className="button button-secondary">
            Зарегистрироваться
          </Link>
        </div>
      </section>
    </main>
  );
}