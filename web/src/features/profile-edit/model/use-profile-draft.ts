import { useState } from 'react';
import type { ProfileDraft } from '../../../entities/profile/model/profile.types';

const emptyProfileDraft: ProfileDraft = {
  name: '',
  role: '',
  about: '',
  skills: [],
  experience: '',
  education: '',
  github: '',
  portfolio: '',
  telegram: '',
};

export function useProfileDraft() {
  const [draft, setDraft] = useState<ProfileDraft>(emptyProfileDraft);
  const [skillInput, setSkillInput] = useState('');

  const updateDraft = <Field extends keyof ProfileDraft>(field: Field, value: ProfileDraft[Field]) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const addSkill = () => {
    const skill = skillInput.trim();
    if (!skill || draft.skills.includes(skill)) return;

    setDraft((current) => ({ ...current, skills: [...current.skills, skill] }));
    setSkillInput('');
  };

  const removeSkill = (skillToRemove: string) => {
    setDraft((current) => ({
      ...current,
      skills: current.skills.filter((skill) => skill !== skillToRemove),
    }));
  };

  return {
    draft,
    skillInput,
    setSkillInput,
    updateDraft,
    addSkill,
    removeSkill,
  };
}
