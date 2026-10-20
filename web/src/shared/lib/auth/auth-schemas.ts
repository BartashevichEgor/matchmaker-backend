import { z } from 'zod';

export const emailSchema = z.string().trim().min(1, 'Введите email').email('Введите корректный email');

export const usernameSchema = z.string().trim().min(1, 'Введите имя пользователя').max(50, 'Имя пользователя слишком длинное');

export const passwordSchema = z.string().min(8, 'Пароль должен содержать не менее 8 символов');

export const credentialsSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
});

export const registerInputSchema = credentialsSchema.extend({
  username: usernameSchema,
});

export const registerFormSchema = registerInputSchema
  .extend({
    confirmPassword: z.string().min(1, 'Подтвердите пароль'),
  })
  .refine((value) => value.password === value.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Пароли должны совпадать',
  });

export function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

export function normalizeUsername(username: string) {
  return username.trim();
}
