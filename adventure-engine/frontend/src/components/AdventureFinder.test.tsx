import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import AdventureFinder from './AdventureFinder';
import { ApiError } from '../services/api';
import * as recommendationsService from '../services/recommendations';
import type { Recommendation } from '../services/types';

function renderWithProviders() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdventureFinder />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const mockRecommendation: Recommendation = {
  destination: {
    id: 1,
    name: 'Banff National Park',
    country: 'Canada',
    region: 'North America',
    description: 'Alpine lakes and mountain hikes.',
    budget_per_day: 220,
    interests: ['hiking', 'scenery'],
    uniqueness_score: 7,
    travel_difficulty: 4,
    latitude: 51.4968,
    longitude: -115.9281,
  },
  adventure_score: 82.3,
  score_breakdown: {
    budget_fit: 0.8,
    interest_match: 1,
    uniqueness: 0.7,
    cost_efficiency: 0.6,
    travel_difficulty: 0.6,
  },
};

describe('AdventureFinder', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows a loading state then renders recommendation cards', async () => {
    vi.spyOn(recommendationsService, 'getRecommendations').mockResolvedValue([mockRecommendation]);

    renderWithProviders();

    expect(screen.getByText(/loading recommendations/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/banff national park, canada/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/82\.3 \/ 100/)).toBeInTheDocument();
  });

  it('shows an error banner with a working retry button', async () => {
    const getRecommendations = vi
      .spyOn(recommendationsService, 'getRecommendations')
      .mockRejectedValueOnce(new ApiError('Could not reach the backend API. Is it running?', 0))
      .mockResolvedValueOnce([mockRecommendation]);

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText(/could not reach the backend api/i)).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /try again/i }));

    await waitFor(() => {
      expect(screen.getByText(/banff national park, canada/i)).toBeInTheDocument();
    });
    expect(getRecommendations).toHaveBeenCalledTimes(2);
  });

  it('submits budget and selected interests as query params', async () => {
    const getRecommendations = vi.spyOn(recommendationsService, 'getRecommendations').mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithProviders();

    await waitFor(() => expect(getRecommendations).toHaveBeenCalledTimes(1));

    await user.type(screen.getByLabelText(/max budget per day/i), '150');
    await user.click(screen.getByRole('button', { name: 'hiking' }));
    await user.click(screen.getByRole('button', { name: /find my trip/i }));

    await waitFor(() => expect(getRecommendations).toHaveBeenCalledTimes(2));
    expect(getRecommendations).toHaveBeenLastCalledWith({ maxBudget: 150, interests: 'hiking' });
  });
});
