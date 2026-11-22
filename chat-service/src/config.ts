import { z } from 'zod';

const schema = z.object({
  CHAT_PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  CHAT_DATABASE_URL: z.url(),
  MATCHMAKER_API_URL: z.url().transform((value) => value.replace(/\/$/, '')),
  CHAT_ALLOWED_ORIGINS: z.string()
    .default('http://localhost:5173,http://127.0.0.1:5173')
    .transform((value) => value.split(',').map((origin) => origin.trim()).filter(Boolean))
    .pipe(z.array(z.url()).refine((origins) => origins.every((origin) => {
      const parsed = new URL(origin);
      return ['http:', 'https:'].includes(parsed.protocol) && parsed.origin === origin;
    }))),
  CHAT_INTERNAL_TIMEOUT_MS: z.coerce.number().int().min(100).max(30000).default(3000),
});

export function loadConfig(env: NodeJS.ProcessEnv = process.env) {
  return schema.parse(env);
}

export type Config = ReturnType<typeof loadConfig>;
