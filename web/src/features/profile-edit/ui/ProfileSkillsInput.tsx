type ProfileSkillsInputProps = {
  skills: string[];
  value: string;
  onChange: (value: string) => void;
  onAdd: () => void;
  onRemove: (skill: string) => void;
};

export function ProfileSkillsInput({
  skills,
  value,
  onChange,
  onAdd,
  onRemove,
}: ProfileSkillsInputProps) {
  return (
    <>
      <div className="create-profile-chips" aria-live="polite">
        {skills.map((skill) => (
          <button
            className="create-profile-chip"
            key={skill}
            type="button"
            aria-label={`Удалить навык ${skill}`}
            onClick={() => onRemove(skill)}
          >
            {skill}
          </button>
        ))}
      </div>
      <div className="create-profile-add-skill">
        <input
          value={value}
          placeholder="Добавить навык"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              onAdd();
            }
          }}
        />
        <button type="button" aria-label="Добавить навык" onClick={onAdd}>＋</button>
      </div>
    </>
  );
}
