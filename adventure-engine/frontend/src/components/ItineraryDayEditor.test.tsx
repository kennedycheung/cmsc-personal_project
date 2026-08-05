import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import ItineraryDayEditor from './ItineraryDayEditor';
import * as activitiesService from '../services/activities';
import * as routingService from '../services/routing';
import type { Activity, DayItinerary } from '../services/types';

function fakeActivity(overrides: Partial<Activity>): Activity {
  return {
    id: 1,
    destination_id: 1,
    name: 'Activity',
    description: null,
    category: null,
    tags: null,
    neighborhood: null,
    price: 10,
    duration_hours: 1,
    location: null,
    opening_time: null,
    closing_time: null,
    travel_minutes: 15,
    latitude: 0,
    longitude: 0,
    ...overrides,
  };
}

function fakeDay(): DayItinerary {
  return {
    day: 1,
    total_cost: 30,
    total_travel_minutes: 30,
    activities: [
      { activity: fakeActivity({ id: 1, name: 'Museum Visit', price: 20 }), start_time: '09:00', end_time: '10:00' },
      { activity: fakeActivity({ id: 2, name: 'Lunch', price: 10 }), start_time: '10:15', end_time: '11:00' },
    ],
  };
}

function renderEditor(day: DayItinerary, onChange: (day: DayItinerary) => void) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ItineraryDayEditor
        destinationId={1}
        day={day}
        totalDays={1}
        otherDaysActivityIds={[]}
        selectedActivityId={null}
        onSelectActivity={() => {}}
        onChange={onChange}
      />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ItineraryDayEditor', () => {
  it('removes a stop and reports the updated day', async () => {
    vi.spyOn(routingService, 'getWalkingRoute').mockResolvedValue({ points: [], durationMinutes: 20 });
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderEditor(fakeDay(), onChange);

    const removeButtons = await screen.findAllByRole('button', { name: /remove/i });
    await user.click(removeButtons[0]);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        day: 1,
        activities: [expect.objectContaining({ activity: expect.objectContaining({ name: 'Lunch' }) })],
      }),
    );
  });

  it('swaps a stop for a fetched alternative', async () => {
    vi.spyOn(routingService, 'getWalkingRoute').mockResolvedValue({ points: [], durationMinutes: 20 });
    vi.spyOn(activitiesService, 'getActivityAlternatives').mockResolvedValue([
      fakeActivity({ id: 3, name: 'Alternative Gallery' }),
    ]);
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderEditor(fakeDay(), onChange);

    const swapButtons = await screen.findAllByRole('button', { name: /swap/i });
    await user.click(swapButtons[0]);

    const alternativeButton = await screen.findByRole('button', { name: 'Alternative Gallery' });
    await user.click(alternativeButton);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        day: 1,
        activities: expect.arrayContaining([
          expect.objectContaining({ activity: expect.objectContaining({ id: 3, name: 'Alternative Gallery' }) }),
        ]),
      }),
    );
  });
});
