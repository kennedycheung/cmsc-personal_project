import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';

import { LOCAL_ACTIVITY_GROUPS } from '../constants';
import { useAdventureRecommendations } from '../hooks/useAdventureRecommendations';
import { ApiError } from '../services/api';
import { resolveLocation } from '../services/geocode';
import type { AdventureRecommendation } from '../services/types';

function RecommendationCard({ recommendation, rank }: { recommendation: AdventureRecommendation; rank: number }) {
  const [showReasons, setShowReasons] = useState(false);

  return (
    <article className='result-card'>
      <h4>
        #{rank} · Score {(recommendation.total_score * 100).toFixed(0)}/100
      </h4>
      <p>{recommendation.summary}</p>
      <p className='map-fallback-note'>Confidence: {(recommendation.confidence * 100).toFixed(0)}% (data completeness)</p>

      <button type='button' className='button button--secondary button--tiny' onClick={() => setShowReasons((v) => !v)}>
        {showReasons ? 'Hide reasoning' : 'Why this ranked here'}
      </button>

      {showReasons && (
        <ul>
          {recommendation.reasons.map((reason) => (
            <li key={reason.factor}>
              <strong>{reason.factor.replace('_', ' ')}:</strong> {reason.reason} (score {reason.score.toFixed(2)})
            </li>
          ))}
        </ul>
      )}

      <h5>Activities</h5>
      <ul>
        {recommendation.activities.map((activity) => (
          <li key={activity.name}>
            {activity.name} <em>({activity.category})</em>
          </li>
        ))}
      </ul>

      {recommendation.itinerary && recommendation.itinerary.slots.length > 0 && (
        <>
          <h5>Suggested itinerary</h5>
          <ul>
            {recommendation.itinerary.slots.map((slot) => (
              <li key={slot.slot}>
                <strong>{slot.slot.replace('_', ' ')}</strong> ({slot.start_time}–{slot.end_time}):{' '}
                {slot.activity.name}
                {slot.walking_minutes_from_previous !== null && ` · ~${slot.walking_minutes_from_previous} min walk`}
              </li>
            ))}
          </ul>
          {recommendation.itinerary.optional_activities.length > 0 && (
            <p>
              <strong>Optional:</strong>{' '}
              {recommendation.itinerary.optional_activities.map((a) => a.name).join(', ')}
            </p>
          )}
        </>
      )}
    </article>
  );
}

export default function AdventuresPage() {
  const [locationInput, setLocationInput] = useState('');
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [geocodeErrorMessage, setGeocodeErrorMessage] = useState<string | null>(null);
  const [resolvedLabel, setResolvedLabel] = useState<string | null>(null);

  const recommendMutation = useAdventureRecommendations();

  const toggleGroup = (group: string) => {
    setSelectedGroups((current) =>
      current.includes(group) ? current.filter((item) => item !== group) : [...current, group],
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
      recommendMutation.mutate({
        latitude: origin.latitude,
        longitude: origin.longitude,
        locationLabel: origin.label,
        interests: selectedGroups,
      });
    } catch (error) {
      setGeocodeErrorMessage(error instanceof ApiError ? error.message : 'Could not resolve that location.');
    } finally {
      setIsGeocoding(false);
    }
  };

  const isLoading = isGeocoding || recommendMutation.isPending;

  return (
    <main className='home-page' id='main-content'>
      <p>
        <Link to='/'>&larr; Back to Adventure Finder</Link>
      </p>

      <section className='section-card'>
        <h1>Adventure Recommendation Engine</h1>
        <p>
          Discovers real nearby activities from OpenStreetMap, clusters them into coherent adventures, and ranks
          them with real reasoning -- no paid API required.
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
              {LOCAL_ACTIVITY_GROUPS.map((group) => (
                <button
                  key={group.value}
                  type='button'
                  aria-pressed={selectedGroups.includes(group.value)}
                  className={selectedGroups.includes(group.value) ? 'chip chip--active' : 'chip'}
                  onClick={() => toggleGroup(group.value)}
                >
                  {group.label}
                </button>
              ))}
            </div>
          </div>

          <div className='finder-actions'>
            <button className='button button--primary' type='submit' disabled={isLoading}>
              {isLoading ? 'Finding adventures…' : 'Recommend adventures'}
            </button>
          </div>
        </form>

        {isLoading && (
          <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
            <span className='spinner' aria-hidden='true' />
            {isGeocoding ? 'Resolving location…' : 'Discovering and scoring nearby adventures…'}
          </div>
        )}

        {geocodeErrorMessage && !isLoading && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>{geocodeErrorMessage}</p>
          </div>
        )}

        {recommendMutation.isError && !isLoading && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>
              {recommendMutation.error instanceof ApiError
                ? recommendMutation.error.message
                : 'Could not run the recommendation engine.'}
            </p>
          </div>
        )}
      </section>

      {recommendMutation.data && !isLoading && (
        <section className='section-card'>
          {resolvedLabel && <p className='map-fallback-note'>Results near {resolvedLabel}</p>}

          {recommendMutation.data.warnings.map((warning) => (
            <p key={warning} className='itinerary-warning'>
              {warning}
            </p>
          ))}

          {recommendMutation.data.recommendations.length === 0 && !recommendMutation.data.warnings.length && (
            <p>No nearby activities found for this location and radius.</p>
          )}

          <div className='result-grid'>
            {recommendMutation.data.recommendations.map((recommendation, index) => (
              <RecommendationCard
                key={`${recommendation.latitude}-${recommendation.longitude}`}
                recommendation={recommendation}
                rank={index + 1}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
