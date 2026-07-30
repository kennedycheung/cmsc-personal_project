import { FormEvent, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import AdventureMap from '../components/AdventureMap';
import { AVAILABLE_INTERESTS } from '../constants';
import { useDestination, useDestinationActivities } from '../hooks/useDestinationDetail';
import { useItinerary } from '../hooks/useItinerary';
import { ApiError } from '../services/api';

export default function DestinationPage() {
  const { id } = useParams<{ id: string }>();
  const destinationId = Number(id);

  const destinationQuery = useDestination(destinationId);
  const activitiesQuery = useDestinationActivities(destinationId);

  const [daysInput, setDaysInput] = useState('3');
  const [budgetInput, setBudgetInput] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [itineraryParams, setItineraryParams] = useState<{ days: number; budget?: number; interests?: string } | null>(
    null,
  );

  const itineraryQuery = useItinerary(destinationId, itineraryParams ?? { days: 3 }, itineraryParams !== null);

  const toggleInterest = (interest: string) => {
    setSelectedInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const days = Math.min(14, Math.max(1, Number(daysInput) || 3));
    const budget = budgetInput ? Number(budgetInput) : undefined;
    setItineraryParams({
      days,
      budget: budget && !Number.isNaN(budget) ? budget : undefined,
      interests: selectedInterests.length > 0 ? selectedInterests.join(',') : undefined,
    });
  };

  if (!Number.isFinite(destinationId)) {
    return (
      <main className='home-page' id='main-content'>
        <div className='status-banner status-banner--error' role='alert'>
          <p>Invalid destination.</p>
        </div>
      </main>
    );
  }

  if (destinationQuery.isLoading) {
    return (
      <main className='home-page' id='main-content'>
        <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
          <span className='spinner' aria-hidden='true' />
          Loading destination…
        </div>
      </main>
    );
  }

  if (destinationQuery.isError || !destinationQuery.data) {
    return (
      <main className='home-page' id='main-content'>
        <div className='status-banner status-banner--error' role='alert'>
          <p>
            {destinationQuery.error instanceof ApiError
              ? destinationQuery.error.message
              : 'Could not load this destination.'}
          </p>
        </div>
      </main>
    );
  }

  const destination = destinationQuery.data;
  const activities = activitiesQuery.data ?? [];

  return (
    <main className='home-page' id='main-content'>
      <p>
        <Link to='/'>&larr; Back to Adventure Finder</Link>
      </p>

      <section className='section-card'>
        <h1>
          {destination.name}, {destination.country}
        </h1>
        <p>{destination.description}</p>
        <ul>
          <li>
            <strong>Region:</strong> {destination.region}
          </li>
          <li>
            <strong>Budget:</strong> ${destination.budget_per_day.toLocaleString()} / day
          </li>
          <li>
            <strong>Interests:</strong> {destination.interests.join(', ') || 'Not specified'}
          </li>
        </ul>
      </section>

      <section className='section-card'>
        <h2>Map</h2>
        <p className='map-fallback-note'>
          Interactive map — the same destination, activities, and itinerary details are also listed as text below.
        </p>
        <div role='img' aria-label={`Map of ${destination.name} showing the destination and nearby activities`}>
          <AdventureMap destination={destination} activities={activities} itineraryDays={itineraryQuery.data?.days} />
        </div>
      </section>

      <section className='section-card'>
        <h2>Plan an itinerary</h2>
        <form className='finder-form' onSubmit={handleSubmit}>
          <div className='finder-grid'>
            <label>
              Days
              <input
                type='number'
                min='1'
                max='14'
                value={daysInput}
                onChange={(event) => setDaysInput(event.target.value)}
              />
            </label>
            <label>
              Total budget ($)
              <input
                type='number'
                min='0'
                placeholder='e.g. 600'
                value={budgetInput}
                onChange={(event) => setBudgetInput(event.target.value)}
              />
            </label>
          </div>

          <div className='form-row form-row--full'>
            <span className='field-label'>Interests</span>
            <div className='checkbox-grid'>
              {AVAILABLE_INTERESTS.map((interest) => (
                <button
                  key={interest}
                  type='button'
                  aria-pressed={selectedInterests.includes(interest)}
                  className={selectedInterests.includes(interest) ? 'chip chip--active' : 'chip'}
                  onClick={() => toggleInterest(interest)}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>

          <div className='finder-actions'>
            <button className='button button--primary' type='submit'>
              Generate itinerary
            </button>
          </div>
        </form>

        {itineraryQuery.isFetching && (
          <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
            <span className='spinner' aria-hidden='true' />
            Generating itinerary…
          </div>
        )}

        {itineraryQuery.isError && !itineraryQuery.isFetching && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>
              {itineraryQuery.error instanceof ApiError
                ? itineraryQuery.error.message
                : 'Could not generate an itinerary.'}
            </p>
            <button className='button button--secondary' type='button' onClick={() => itineraryQuery.refetch()}>
              Try again
            </button>
          </div>
        )}

        {itineraryQuery.data && !itineraryQuery.isFetching && (
          <div className='result-grid'>
            {itineraryQuery.data.warnings.map((warning) => (
              <p key={warning} className='itinerary-warning'>
                {warning}
              </p>
            ))}
            {itineraryQuery.data.days.map((day) => (
              <article key={day.day} className='result-card'>
                <h4>Day {day.day}</h4>
                {day.activities.length === 0 ? (
                  <p>No activities scheduled.</p>
                ) : (
                  <ul>
                    {day.activities.map((item) => (
                      <li key={item.activity.id}>
                        <strong>
                          {item.start_time}–{item.end_time}
                        </strong>{' '}
                        {item.activity.name} (${item.activity.price})
                      </li>
                    ))}
                  </ul>
                )}
                <p>
                  <strong>Day total:</strong> ${day.total_cost} · {day.total_travel_minutes} min travel
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className='section-card'>
        <h2>Activities</h2>
        {activities.length === 0 ? (
          <p>No stored activities for this destination yet.</p>
        ) : (
          <div className='result-grid'>
            {activities.map((activity) => (
              <article key={activity.id} className='result-card'>
                <h4>{activity.name}</h4>
                <p>{activity.description}</p>
                <ul>
                  <li>
                    <strong>Category:</strong> {activity.category ?? 'Uncategorized'}
                  </li>
                  <li>
                    <strong>Price:</strong> {activity.price > 0 ? `$${activity.price}` : 'Free'}
                  </li>
                  {activity.location && (
                    <li>
                      <strong>Location:</strong> {activity.location}
                    </li>
                  )}
                  {(activity.opening_time || activity.closing_time) && (
                    <li>
                      <strong>Hours:</strong> {activity.opening_time ?? '—'} – {activity.closing_time ?? '—'}
                    </li>
                  )}
                </ul>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
