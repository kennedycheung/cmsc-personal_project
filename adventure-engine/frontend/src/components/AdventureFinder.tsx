import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';

import { AVAILABLE_INTERESTS } from '../constants';
import { useRecommendations } from '../hooks/useRecommendations';
import { ApiError } from '../services/api';
import type { RecommendationParams } from '../services/recommendations';

export default function AdventureFinder() {
  const [budgetInput, setBudgetInput] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [queryParams, setQueryParams] = useState<RecommendationParams>({});

  const { data: recommendations, isLoading, isFetching, isError, error, refetch } =
    useRecommendations(queryParams);

  const toggleInterest = (interest: string) => {
    setSelectedInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const maxBudget = Number(budgetInput);
    setQueryParams({
      maxBudget: budgetInput && !Number.isNaN(maxBudget) ? maxBudget : undefined,
      interests: selectedInterests.length > 0 ? selectedInterests.join(',') : undefined,
    });
  };

  return (
    <section className='finder-panel'>
      <div className='finder-panel__intro'>
        <h2>Adventure Finder</h2>
        <p>Set a daily budget and pick a few interests to rank real destinations from the backend.</p>
      </div>

      <form className='finder-form' onSubmit={handleSubmit}>
        <div className='finder-grid'>
          <label>
            Max budget per day ($)
            <input
              type='number'
              min='0'
              placeholder='e.g. 150'
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
            Find my trip
          </button>
        </div>
      </form>

      <div className='finder-results'>
        <h3>Trip recommendations</h3>

        {(isLoading || isFetching) && (
          <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
            <span className='spinner' aria-hidden='true' />
            Loading recommendations…
          </div>
        )}

        {isError && !isFetching && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>{error instanceof ApiError ? error.message : 'Something went wrong loading recommendations.'}</p>
            <button className='button button--secondary' type='button' onClick={() => refetch()}>
              Try again
            </button>
          </div>
        )}

        {!isLoading && !isFetching && !isError && recommendations && recommendations.length === 0 && (
          <p>No matched trips found. Try a higher budget or different interests.</p>
        )}

        {!isFetching && !isError && recommendations && recommendations.length > 0 && (
          <div className='result-grid'>
            {recommendations.map((item) => (
              <article key={item.destination.id} className='result-card'>
                <h4>
                  {item.destination.name}, {item.destination.country}
                </h4>
                <p>{item.destination.description}</p>
                <ul>
                  <li>
                    <strong>Adventure score:</strong> {item.adventure_score.toFixed(1)} / 100
                  </li>
                  <li>
                    <strong>Estimated cost:</strong> ${item.destination.budget_per_day.toLocaleString()} / day
                  </li>
                  <li>
                    <strong>Region:</strong> {item.destination.region}
                  </li>
                  {item.destination.interests.length > 0 && (
                    <li>
                      <strong>Interests:</strong> {item.destination.interests.join(', ')}
                    </li>
                  )}
                </ul>
                <Link className='result-card__link' to={`/destinations/${item.destination.id}`}>
                  View on map &amp; plan itinerary &rarr;
                </Link>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
