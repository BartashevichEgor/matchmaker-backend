import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../app/providers/AuthProvider';
import { ProfileAvatar } from '../../entities/profile/ui/ProfileAvatar';
import { Accordion } from '../../shared/ui/Accordion';

export function ProfilePage() {
  const { user } = useAuth();
  const username = user?.username ?? 'Veronika';
  const avatarName = user?.username ?? 'Имя Фамилия';
  const [openSections, setOpenSections] = useState({ experience: false, links: false });

  return (
    <section className="profile-page" aria-labelledby="profile-title">
      <h1 id="profile-title" aria-label="Профиль">Мой профиль</h1>
      <div className="profile-layout">
        <article className="profile-card">
          <ProfileAvatar name={avatarName} className="profile-card__avatar" />
          <h2>@{username}</h2>
          <p>UI/UX-дизайнер</p>
          <Link className="button button-primary profile-card__edit" to="/profile/create?step=1">
            Редактировать
          </Link>
        </article>

        <div className="profile-details">
          <div className="profile-stats">
            <div><strong>12</strong><span>мэтчей</span></div>
            <div><strong>48</strong><span>лайков</span></div>
          </div>
          <section>
            <h2>О себе</h2>
            <p>Рисую интерфейсы и люблю проекты, которые приносят пользу.</p>
          </section>
          <section>
            <h2>Стек и навыки</h2>
            <div className="profile-chips"><span>Figma</span><span>UX</span><span>Mermaid</span></div>
          </section>
          <Accordion
            className="profile-accordion"
            title="Опыт и образование"
            open={openSections.experience}
            onToggle={() => setOpenSections((current) => ({ ...current, experience: !current.experience }))}
          >
            <div className="profile-accordion__details">
              <div><h3>Опыт работы</h3><p>Учебные и личные проекты в дизайне интерфейсов.</p></div>
              <div><h3>Образование</h3><p>Дизайн интерфейсов и пользовательский опыт.</p></div>
            </div>
          </Accordion>
          <Accordion
            className="profile-accordion"
            title="GitHub и ссылки"
            open={openSections.links}
            onToggle={() => setOpenSections((current) => ({ ...current, links: !current.links }))}
          >
            <div className="profile-accordion__details">
              <div><h3>GitHub</h3><a href="https://github.com" target="_blank" rel="noreferrer">github.com/username</a></div>
              <div><h3>Портфолио</h3><a href="https://example.com" target="_blank" rel="noreferrer">your-portfolio.example</a></div>
            </div>
          </Accordion>
        </div>
      </div>
    </section>
  );
}
