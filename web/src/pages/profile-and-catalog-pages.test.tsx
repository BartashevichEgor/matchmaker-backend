import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CatalogPage } from './catalog/CatalogPage';
import { CreateProfilePage } from './profile/CreateProfilePage';

describe('profile and catalog interactions', () => {
  it('updates photo initials and removes a skill from the profile form', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/profile/create?step=1']}>
        <CreateProfilePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText('Имя и фамилия *'), 'Анна Иванова');
    expect(screen.getByRole('button', { name: 'Добавить фото' })).toHaveTextContent('АИ');

    await user.click(screen.getByRole('button', { name: /Далее: навыки и опыт/i }));
    await user.type(screen.getByPlaceholderText('Добавить навык'), 'Figma');
    await user.click(screen.getByRole('button', { name: 'Добавить навык' }));
    expect(screen.getByText('Figma')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Удалить навык Figma' }));
    expect(screen.queryByText('Figma')).not.toBeInTheDocument();
  });

  it('opens the related fields in profile creation and catalog filters', async () => {
    const user = userEvent.setup();

    const { unmount } = render(
      <MemoryRouter initialEntries={['/profile/create?step=2']}>
        <CreateProfilePage />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText('https://github.com/username')).not.toBeVisible();
    await user.click(screen.getByRole('button', { name: 'GitHub и ссылки' }));
    expect(screen.getByPlaceholderText('https://github.com/username')).toBeInTheDocument();
    unmount();

    render(<CatalogPage />);
    expect(screen.getByPlaceholderText('От 1 года')).not.toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Дополнительно' }));
    expect(screen.getByPlaceholderText('От 1 года')).toBeInTheDocument();
  });
});
