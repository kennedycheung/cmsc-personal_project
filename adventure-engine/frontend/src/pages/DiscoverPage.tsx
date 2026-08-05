import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';

import { DISCOVERY_INTERESTS } from '../constants';
import { useDiscovery } from '../hooks/useDiscovery';
import { ApiError } from '../services/api';
import { resolveLocation } from '../services/geocode';
import type { DiscoveredAttraction, RecommendationBuckets } from '../services/types';

const BUCKET_LABELS: { key: keyof RecommendationBuckets; label: string }[] = [
  { key: 'best_overall', label: 'Best Overall' },
  { key: 'best_value', label: 'Best Value' },
  { key: 'best_hidden_gem', label: 'Best Hidden Gem' },
  { key: 'best_family', label: 'Best Family Activity' },
  { key: 'best_evening', label: 'Best Evening Activity' },
  { key: 'best_rainy_day', label: 'Best Rainy Day Activity' },
  { key: 'best_free', label: 'Best Free Activity' },
];

function AttractionCard({ attraction }: { attraction: DiscoveredAttraction }) {
  return (
    <article className='result-card'>
      <h4>{attraction.name}</h4>
      <ul>
        {attraction.rating !== null && (
          <li>
            <strong>Rating:</strong> {attraction.rating.toFixed(1)}
            {attraction.review_count !== null && ` (${attraction.review_count.toLocaleString()} reviews)`}
          </li>
        )}
        {attraction.price_level !== null && (
          <li>
            <strong>Price:</strong> {attraction.price_level === 0 ? 'Free' : '$'.repeat(attraction.price_level)}
          </li>
        )}
        {attraction.address && (
          <li>
            <strong>Address:</strong> {attraction.address}
          </li>
        )}
        {attraction.categories.length > 0 && (
          <li>
            <strong>Categories:</strong> {attraction.categories.slice(0, 4).join(', ')}
          </li>
        )}
        {attraction.review_summary && (
          <li>
            <strong>Reviews say:</strong> {attraction.review_summary}
          </li>
        )}
        <li>
          <strong>Sources:</strong> {attraction.engines.join(', ')}
        </li>
      </ul>
    </article>
  );
}

export default function DiscoverPage() {
  const [locationInput, setLocationInput] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [geocodeErrorMessage, setGeocodeErrorMessage] = useState<string | null>(null);
  const [resolvedLabel, setResolvedLabel] = useState<string | null>(null);

  const discoveryMutation = useDiscovery();

  const toggleInterest = (interest: string) => {
    setSelectedInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!locationInput.trim()) return;

    setGeocodeErrorMessage(null);
    setIsGeocoding(true);
    try {
      const origin = await resolveLocation(locationInput);
      setResolvedLabel(origin.label);
      discoveryMutation.mutate({
        latitude: origin.latitude,
        longitude: origin.longitude,
        locationLabel: origin.label,
        interests: selectedInterests,
      });
    } catch (error) {
      setGeocodeErrorMessage(
        error instanceof ApiError ? error.message : 'Could not resolve that location.',
      );
    } finally {
      setIsGeocoding(false);
    }
  };

  const isLoading = isGeocoding || discoveryMutation.isPending;

  return (
    <main className='home-page' id='main-content'>
      <p>
        <Link to='/'>&larr; Back to Adventure Finder</Link>
      </p>

      <section className='section-card'>
        <h1>Activity Discovery Engine</h1>
        <p>
          Aggregates real search results across Google Events, Google Maps, TripAdvisor, and Yelp, then ranks and
          groups them into recommendation buckets.
        </p>

        <form className='finder-form' onSubmit={handleSubmit}>
          <div className='finder-grid'>
            <label>
              City or place
              <input
                type='text'
                placeholder='e.g. Chicago'
                value={locationInput}
                onChange={(event) => setLocationInput(event.target.value)}
              />
            </label>
          </div>

          <div className='form-row form-row--full'>
            <span className='field-label'>Interests</span>
            <div className='checkbox-grid'>
              {DISCOVERY_INTERESTS.map((interest) => (
                <button
                  key={interest}
                  type='button'
                  aria-pressed={selectedInterests.includes(interest)}
                  className={selectedInterests.includes(interest) ? 'chip chip--active' : 'chip'}
                  onClick={() => toggleInterest(interest)}
                >
                  {interest.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className='finder-actions'>
            <button className='button button--primary' type='submit' disabled={isLoading}>
              {isLoading ? 'Searching…' : 'Find activities'}
            </button>
          </div>
        </form>

        {isLoading && (
          <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
            <span className='spinner' aria-hidden='true' />
            {isGeocoding ? 'Resolving location…' : 'Searching Google, TripAdvisor, and Yelp…'}
          </div>
        )}

        {geocodeErrorMessage && !isLoading && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>{geocodeErrorMessage}</p>
          </div>
        )}

        {discoveryMutation.isError && !isLoading && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>
              {discoveryMutation.error instanceof ApiError
                ? discoveryMutation.error.message
                : 'Could not run the discovery engine.'}
            </p>
          </div>
        )}
      </section>

      {discoveryMutation.data && !isLoading && (
        <>
          {resolvedLabel && <p className='map-fallback-note'>Results for {resolvedLabel}</p>}

          {discoveryMutation.data.warnings.map((warning) => (
            <p key={warning} className='itinerary-warning'>
              {warning}
            </p>
          ))}

          {BUCKET_LABELS.map(({ key, label }) => {
            const attractions = discoveryMutation.data!.buckets[key];
            if (attractions.length === 0) return null;
            return (
              <section className='section-card' key={key}>
                <h2>{label}</h2>
                <div className='result-grid'>
                  {attractions.map((attraction) => (
                    <AttractionCard key={`${key}-${attraction.name}`} attraction={attraction} />
                  ))}
                </div>
              </section>
            );
          })}

          {discoveryMutation.data.route && (
            <section className='section-card'>
              <h2>Suggested route</h2>
              <p>
                <strong>Total walking time:</strong> {discoveryMutation.data.route.total_duration_minutes} min
              </p>
              <ol>
                {discoveryMutation.data.route.legs.map((leg, index) => (
                  <li key={index}>
                    {leg.from_name} → {leg.to_name}: {leg.distance_text}, {leg.duration_text}
                  </li>
                ))}
              </ol>
            </section>
          )}
        </>
      )}
    </main>
  );
}
