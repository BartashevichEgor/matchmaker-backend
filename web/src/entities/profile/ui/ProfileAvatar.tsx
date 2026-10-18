import { getProfileInitials } from '../lib/get-profile-initials';

type ProfileAvatarProps = {
  name: string;
  className?: string;
};

export function ProfileAvatar({ name, className = '' }: ProfileAvatarProps) {
  return <div className={`profile-avatar ${className}`.trim()}>{getProfileInitials(name)}</div>;
}
