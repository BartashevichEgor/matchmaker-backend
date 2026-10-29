export function getProfileInitials(name: string): string {
  const words = name.trim().split(/[\s_-]+/).filter(Boolean);

  if (words.length >= 2) {
    return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
  }

  if (words.length === 1) {
    return `${words[0][0]}${words[0][1] ?? words[0][0]}`.toUpperCase();
  }

  return 'ИИ';
}
