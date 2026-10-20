export function AppLoader() {
  return (
    <main className="app-loader" aria-busy="true" aria-label="Загрузка приложения">
      <div className="app-loader__content">
        <img src="/assets/matchmaker-logo.png" alt="" />
        <h1>Matchmaker</h1>
        <p>Команда начинается с мэтча</p>
        <div className="app-loader__progress" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <small>Загружаем приложение</small>
      </div>
    </main>
  );
}
