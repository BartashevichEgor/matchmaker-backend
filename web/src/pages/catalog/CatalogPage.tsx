import { useState } from 'react';
import { Accordion } from '../../shared/ui/Accordion';

type CatalogMode = 'specialists' | 'projects';

function CrossIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="catalog-action-icon">
      <path d="m7 7 10 10M17 7 7 17" />
    </svg>
  );
}

function HeartIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="catalog-action-icon">
      <path d="M20.5 8.8c0 5.2-8.5 10.2-8.5 10.2S3.5 14 3.5 8.8A4.4 4.4 0 0 1 12 7.1a4.4 4.4 0 0 1 8.5 1.7Z" />
    </svg>
  );
}

function FilterIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="catalog-filter-icon">
      <path d="M4 7h16M4 17h16M9 7a2 2 0 1 0 0 0.01M15 17a2 2 0 1 0 0 0.01" />
    </svg>
  );
}

function FilterField({ label, placeholder }: { label: string; placeholder: string }) {
  return (
    <label className="catalog-filter__field">
      <span>{label}</span>
      <input placeholder={placeholder} />
    </label>
  );
}

export function CatalogPage() {
  const [mode, setMode] = useState<CatalogMode>('specialists');
  const [isAdvancedFiltersOpen, setIsAdvancedFiltersOpen] = useState(false);

  return (
    <section className="catalog-page" aria-labelledby="catalog-title">
      <div className="catalog-page__heading">
        <h1 id="catalog-title" aria-label="Лента — Каталог">Каталог</h1>
        <span className="catalog-page__filter-icon" aria-hidden="true">
          <FilterIcon />
        </span>
      </div>

      <div className="catalog-layout">
        <aside className="catalog-filter" aria-label="Фильтры каталога">
          <h2>Фильтры</h2>
          <FilterField label="Роль" placeholder="Все роли" />
          <FilterField label="Навыки" placeholder="Figma, UX" />
          <Accordion
            className="catalog-filter__collapse"
            title="Дополнительно"
            open={isAdvancedFiltersOpen}
            onToggle={() => setIsAdvancedFiltersOpen((isOpen) => !isOpen)}
          >
            <div className="catalog-filter__advanced">
              <FilterField label="Опыт" placeholder="От 1 года" />
              <FilterField label="Формат работы" placeholder="Удалённо или гибридно" />
            </div>
          </Accordion>
          <button className="button button-primary catalog-filter__submit" type="button">
            Применить
          </button>
        </aside>

        <div className="catalog-results">
          <h2>Подходят тебе</h2>
          <div className="catalog-switcher" role="tablist" aria-label="Тип каталога">
            <button
              className={mode === 'projects' ? 'catalog-switcher__tab catalog-switcher__tab--active' : 'catalog-switcher__tab'}
              type="button"
              role="tab"
              aria-selected={mode === 'projects'}
              onClick={() => setMode('projects')}
            >
              Проекты
            </button>
            <button
              className={mode === 'specialists' ? 'catalog-switcher__tab catalog-switcher__tab--active' : 'catalog-switcher__tab'}
              type="button"
              role="tab"
              aria-selected={mode === 'specialists'}
              onClick={() => setMode('specialists')}
            >
              Специалисты
            </button>
          </div>

          {mode === 'specialists' ? <SpecialistCard /> : <ProjectCard />}
        </div>
      </div>
    </section>
  );
}

function SpecialistCard() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <article className="catalog-card catalog-card--specialist">
      <div className="catalog-card__cover catalog-card__cover--portrait">
        <span className="catalog-card__match">87% совпадение</span>
        <span className="catalog-card__initials">АК</span>
      </div>
      <h3>Алексей Ковалёв</h3>
      <p className="catalog-card__role">Backend-разработчик</p>
      <div className="catalog-card__chips">
        <span>Python</span><span>Django</span><span>SQL</span>
      </div>
      <p className="catalog-card__description">Люблю чистый код. Ищу команду для полезного проекта.</p>
      <Accordion
        className="catalog-card__accordion"
        title="Опыт и GitHub"
        open={isExpanded}
        onToggle={() => setIsExpanded((isOpen) => !isOpen)}
      >
        <div className="catalog-card__accordion-details">
          <p><strong>Опыт:</strong> 3 года в backend-разработке и командных проектах.</p>
          <p><strong>GitHub:</strong> github.com/alexey-k</p>
        </div>
      </Accordion>
      <CatalogActions />
    </article>
  );
}

function ProjectCard() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <article className="catalog-card catalog-card--project">
      <div className="catalog-card__cover catalog-card__cover--project">
        <strong>TeamFlow</strong>
        <span>Сервис для студенческих команд</span>
      </div>
      <h3>TeamFlow</h3>
      <p className="catalog-card__role">Ищем UI/UX-дизайнера</p>
      <div className="catalog-card__chips">
        <span>Figma</span><span>UX</span><span>UI</span>
      </div>
      <p className="catalog-card__description">Создаём планировщик задач. Нужна помощь с интерфейсом и прототипом.</p>
      <Accordion
        className="catalog-card__accordion"
        title="Подробнее о проекте"
        open={isExpanded}
        onToggle={() => setIsExpanded((isOpen) => !isOpen)}
      >
        <div className="catalog-card__accordion-details">
          <p><strong>Задача:</strong> собрать удобный планировщик задач для студенческих команд.</p>
          <p><strong>Формат:</strong> совместная работа и регулярные созвоны.</p>
        </div>
      </Accordion>
      <CatalogActions />
    </article>
  );
}

function CatalogActions() {
  return (
    <div className="catalog-card__actions">
      <button className="catalog-card__action catalog-card__action--reject" type="button" aria-label="Пропустить">
        <CrossIcon />
      </button>
      <button className="catalog-card__action catalog-card__action--like" type="button" aria-label="Добавить в избранное">
        <HeartIcon />
      </button>
    </div>
  );
}
