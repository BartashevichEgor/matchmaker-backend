import { useParams } from 'react-router-dom';

type SectionPlaceholderProps = {
  title: string;
  description: string;
  matchIdFromParams?: boolean;
};

export function SectionPlaceholder({ title, description, matchIdFromParams }: SectionPlaceholderProps) {
  const params = useParams();

  return (
    <div className="page-shell">
      <section className="section-card">
        <p className="section-badge">В разработке</p>
        <h1>{title}</h1>
        <p>{description}</p>
        {matchIdFromParams && params.matchId ? (
          <p className="section-meta">matchId: {params.matchId}</p>
        ) : null}
      </section>
    </div>
  );
}
