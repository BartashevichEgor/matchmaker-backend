import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getProfileInitials } from '../../entities/profile/lib/get-profile-initials';
import { Accordion } from '../../shared/ui/Accordion';
import { useProfileDraft } from '../../features/profile-edit/model/use-profile-draft';
import { ProfileSkillsInput } from '../../features/profile-edit/ui/ProfileSkillsInput';

export function CreateProfilePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(searchParams.get('step') === '2' ? 2 : 1);
  const [openSections, setOpenSections] = useState({ experience: true, links: false });
  const { draft, skillInput, setSkillInput, updateDraft, addSkill, removeSkill } = useProfileDraft();

  return (
    <section className="create-profile-page" aria-labelledby="create-profile-title">
      <aside className="create-profile-intro">
        <h1>Создать<br />профиль</h1>
        <ol>
          <li className={step === 1 ? 'is-active' : ''}><button type="button" onClick={() => setStep(1)}>1. Основное</button></li>
          <li className={step === 2 ? 'is-active' : ''}><button type="button" onClick={() => setStep(2)}>2. Навыки и опыт</button></li>
        </ol>
        <p>Профиль помогает<br />найти подходящую<br />команду.</p>
      </aside>

      <form className="create-profile-form" onSubmit={(event) => event.preventDefault()}>
        <h2 id="create-profile-title">Создание профиля</h2>
        <p className="create-profile-form__step">Шаг {step} из 2 · {step === 1 ? 'Основное' : 'Навыки и опыт'}</p>
        <div className="create-profile-form__progress"><span className={step === 2 ? 'is-complete' : ''} /></div>

        {step === 1 ? (
          <div className="create-profile-form__body">
            <button className="create-profile-photo" type="button" aria-label="Добавить фото">
              <span className="create-profile-photo__avatar">{getProfileInitials(draft.name)}</span>
              <strong>Добавить фото</strong><small>Можно заполнить позже</small>
            </button>
            <label className="create-profile-field"><span>Имя и фамилия *</span><input placeholder="Ваше имя и фамилия" value={draft.name} onChange={(event) => updateDraft('name', event.target.value)} /></label>
            <label className="create-profile-field"><span>Роль *</span><input placeholder="Например, UI/UX-дизайнер" value={draft.role} onChange={(event) => updateDraft('role', event.target.value)} /></label>
            <label className="create-profile-field"><span>О себе</span><textarea placeholder="Расскажите о себе и своих проектах" value={draft.about} onChange={(event) => updateDraft('about', event.target.value)} /></label>
            <small className="create-profile-required">* Обязательные поля</small>
            <button className="button button-primary create-profile-submit" type="button" onClick={() => setStep(2)}>Далее: навыки и опыт</button>
          </div>
        ) : (
          <div className="create-profile-form__body">
            <div className="create-profile-field"><span>Навыки *</span><ProfileSkillsInput skills={draft.skills} value={skillInput} onChange={setSkillInput} onAdd={addSkill} onRemove={removeSkill} /></div>
            <Accordion
              className="create-profile-accordion"
              title="Опыт и образование"
              open={openSections.experience}
              onToggle={() => setOpenSections((current) => ({ ...current, experience: !current.experience }))}
            >
              <label className="create-profile-field"><span>Опыт работы</span><input placeholder="Расскажите об опыте и проектах" value={draft.experience} onChange={(event) => updateDraft('experience', event.target.value)} /></label>
              <label className="create-profile-field"><span>Образование</span><input placeholder="Например, дизайн интерфейсов" value={draft.education} onChange={(event) => updateDraft('education', event.target.value)} /></label>
            </Accordion>
            <Accordion
              className="create-profile-accordion"
              title="GitHub и ссылки"
              open={openSections.links}
              onToggle={() => setOpenSections((current) => ({ ...current, links: !current.links }))}
            >
              <label className="create-profile-field"><span>GitHub</span><input placeholder="https://github.com/username" value={draft.github} onChange={(event) => updateDraft('github', event.target.value)} /></label>
              <label className="create-profile-field"><span>Портфолио или сайт</span><input placeholder="https://your-portfolio.example" value={draft.portfolio} onChange={(event) => updateDraft('portfolio', event.target.value)} /></label>
              <label className="create-profile-field"><span>Telegram</span><input placeholder="@username" value={draft.telegram} onChange={(event) => updateDraft('telegram', event.target.value)} /></label>
            </Accordion>
            <small className="create-profile-required">Дополнительные разделы необязательны</small>
            <button className="button button-primary create-profile-submit" type="button" onClick={() => navigate('/profile')}>Создать профиль</button>
            <button className="create-profile-back" type="button" onClick={() => setStep(1)}>Назад к основному</button>
          </div>
        )}
      </form>
    </section>
  );
}
