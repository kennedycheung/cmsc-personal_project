import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import AdventureWizard from './AdventureWizard';
import * as geocodeService from '../services/geocode';
import * as localActivitiesService from '../services/localActivities';
import * as recommendationsService from '../services/recommendations';

function renderWizard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdventureWizard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const FAKE_ORIGIN = { latitude: 41.88, longitude: -87.63, label: 'Chicago, Illinois, United States', country: 'United States' };

afterEach(() => {
  vi.restoreAllMocks();
});

describe('AdventureWizard', () => {
  it('starts on the origin step', () => {
    renderWizard();
    expect(screen.getByRole('heading', { name: /where are you starting from/i })).toBeInTheDocument();
  });

  it('resolves the origin and advances to the time-selection step', async () => {
    vi.spyOn(geocodeService, 'resolveLocation').mockResolvedValue(FAKE_ORIGIN);
    const user = userEvent.setup();
    renderWizard();

    await user.type(screen.getByLabelText(/city or airport/i), 'Chicago');
    await user.click(screen.getByRole('button', { name: /continue/i }));

    expect(await screen.findByRole('heading', { name: /how much time do you have/i })).toBeInTheDocument();
    expect(screen.getByText(FAKE_ORIGIN.label)).toBeInTheDocument();
  });

  it('a sub-day time bucket skips the branch step and asks for local-adventure categories', async () => {
    vi.spyOn(geocodeService, 'resolveLocation').mockResolvedValue(FAKE_ORIGIN);
    const user = userEvent.setup();
    renderWizard();

    await user.type(screen.getByLabelText(/city or airport/i), 'Chicago');
    await user.click(screen.getByRole('button', { name: /continue/i }));
    await screen.findByRole('heading', { name: /how much time do you have/i });

    await user.click(screen.getByLabelText('Half day'));

    expect(await screen.findByRole('heading', { name: /what are you interested in/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /stay in your current city/i })).not.toBeInTheDocument();
  });

  it('a multi-day time bucket asks the stay-local/travel branch question before trip details', async () => {
    vi.spyOn(geocodeService, 'resolveLocation').mockResolvedValue(FAKE_ORIGIN);
    const user = userEvent.setup();
    renderWizard();

    await user.type(screen.getByLabelText(/city or airport/i), 'Chicago');
    await user.click(screen.getByRole('button', { name: /continue/i }));
    await screen.findByRole('heading', { name: /how much time do you have/i });

    await user.click(screen.getByLabelText('Weekend'));

    expect(await screen.findByRole('heading', { name: /stay in your current city/i })).toBeInTheDocument();
  });

  it('completes the local-adventure path and renders discovered activities', async () => {
    vi.spyOn(geocodeService, 'resolveLocation').mockResolvedValue(FAKE_ORIGIN);
    vi.spyOn(localActivitiesService, 'getLocalActivities').mockResolvedValue({
      origin_label: FAKE_ORIGIN.label,
      radius_km: 15,
      groups: {
        food: [
          {
            name: 'Test Cafe',
            description: null,
            group: 'food',
            category: 'cafe',
            location: 'Chicago',
            latitude: 41.88,
            longitude: -87.63,
            distance_km: 0.5,
            duration_hours: 1,
            is_outdoor: false,
            opening_time: null,
            closing_time: null,
          },
        ],
      },
    });

    const user = userEvent.setup();
    renderWizard();

    await user.type(screen.getByLabelText(/city or airport/i), 'Chicago');
    await user.click(screen.getByRole('button', { name: /continue/i }));
    await screen.findByRole('heading', { name: /how much time do you have/i });

    await user.click(screen.getByLabelText('2 hours'));
    await screen.findByRole('heading', { name: /what are you interested in/i });

    await user.click(screen.getByRole('button', { name: /find nearby activities/i }));

    expect(await screen.findByText('Test Cafe')).toBeInTheDocument();
    expect(localActivitiesService.getLocalActivities).toHaveBeenCalledWith(
      expect.objectContaining({ latitude: FAKE_ORIGIN.latitude, longitude: FAKE_ORIGIN.longitude }),
    );
  });

  it('completes the travel path and renders ranked destination recommendations', async () => {
    vi.spyOn(geocodeService, 'resolveLocation').mockResolvedValue(FAKE_ORIGIN);
    vi.spyOn(recommendationsService, 'getRecommendations').mockResolvedValue([
      {
        destination: {
          id: 1,
          name: 'Banff National Park',
          country: 'Canada',
          region: 'North America',
          description: 'Alpine lakes and mountain hikes.',
          budget_per_day: 220,
          interests: ['hiking'],
          uniqueness_score: 7,
          travel_difficulty: 4,
          latitude: 51.4968,
          longitude: -115.9281,
        },
        adventure_score: 82.5,
        score_breakdown: {
          budget_fit: 1,
          interest_match: 1,
          uniqueness: 0.7,
          cost_efficiency: 0.6,
          travel_difficulty: 0.6,
        },
      },
    ]);

    const user = userEvent.setup();
    renderWizard();

    await user.type(screen.getByLabelText(/city or airport/i), 'Chicago');
    await user.click(screen.getByRole('button', { name: /continue/i }));
    await screen.findByRole('heading', { name: /how much time do you have/i });

    await user.click(screen.getByLabelText('Weekend'));
    await screen.findByRole('heading', { name: /stay in your current city/i });

    await user.click(screen.getByLabelText(/day trip/i));
    await screen.findByRole('heading', { name: /trip details/i });

    await user.click(screen.getByRole('button', { name: /find my trip/i }));

    expect(await screen.findByText(/Banff National Park/)).toBeInTheDocument();
    await waitFor(() =>
      expect(recommendationsService.getRecommendations).toHaveBeenCalledWith(
        expect.objectContaining({ timeBucket: 'weekend', travelScope: 'day_trip' }),
      ),
    );
  });
});
