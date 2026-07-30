import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  AVAILABLE_INTERESTS,
  LOCAL_ACTIVITY_GROUPS,
  LOCAL_ADVENTURE_BUCKET_VALUES,
  TIME_BUCKETS,
  TRAVEL_SCOPES,
} from '../constants';
import { useGeocode } from '../hooks/useGeocode';
import { useLocalActivities } from '../hooks/useLocalActivities';
import { useRecommendations } from '../hooks/useRecommendations';
import { ApiError } from '../services/api';
import type { LocalActivitiesParams } from '../services/localActivities';
import type { RecommendationParams } from '../services/recommendations';

type WizardStep = 'origin' | 'time' | 'branch' | 'details' | 'results';

const STEP_LABELS: Record<Exclude<WizardStep, 'results'>, string> = {
  origin: 'Starting location',
  time: 'Available time',
  branch: 'How far',
  details: 'Trip details',
};

function StepIndicator({ current, isLocalAdventure }: { current: WizardStep; isLocalAdventure: boolean }) {
  const steps: Exclude<WizardStep, 'results'>[] = isLocalAdventure
    ? ['origin', 'time', 'details']
    : ['origin', 'time', 'branch', 'details'];
  const currentIndex = current === 'results' ? steps.length : steps.indexOf(current as Exclude<WizardStep, 'results'>);

  return (
    <ol className='wizard-steps'>
      {steps.map((step, index) => (
        <li
          key={step}
          className={
            index === currentIndex
              ? 'wizard-step-indicator wizard-step-indicator--active'
              : index < currentIndex
                ? 'wizard-step-indicator wizard-step-indicator--done'
                : 'wizard-step-indicator'
          }
        >
          {index + 1}. {STEP_LABELS[step]}
        </li>
      ))}
    </ol>
  );
}

export default function AdventureWizard() {
  const [step, setStep] = useState<WizardStep>('origin');

  // Step 1: starting location
  const [originInput, setOriginInput] = useState('');
  const [originQuery, setOriginQuery] = useState<string | null>(null);
  const {
    data: origin,
    isFetching: isGeocoding,
    isError: isGeocodeError,
    error: geocodeError,
  } = useGeocode(originQuery ?? '', originQuery !== null);

  useEffect(() => {
    if (origin && step === 'origin') {
      setStep('time');
    }
  }, [origin, step]);

  // Step 2: available time
  const [timeBucket, setTimeBucket] = useState<string | null>(null);
  const isLocalAdventure = timeBucket !== null && LOCAL_ADVENTURE_BUCKET_VALUES.has(timeBucket);

  // Step 3: how far (skipped for local adventures)
  const [travelScope, setTravelScope] = useState<string | null>(null);

  // Step 4a: local-adventure category selection
  const [selectedGroups, setSelectedGroups] = useState<string[]>(LOCAL_ACTIVITY_GROUPS.map((g) => g.value));

  // Step 4b: travel trip details
  const [budgetInput, setBudgetInput] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);

  // Results (gated queries -- only fire once step 4 is submitted)
  const [recommendationParams, setRecommendationParams] = useState<RecommendationParams | null>(null);
  const [localActivityParams, setLocalActivityParams] = useState<LocalActivitiesParams | null>(null);

  const {
    data: recommendations,
    isLoading: isLoadingRecs,
    isFetching: isFetchingRecs,
    isError: isRecsError,
    error: recsError,
    refetch: refetchRecs,
  } = useRecommendations(recommendationParams ?? {}, recommendationParams !== null);

  const {
    data: localActivities,
    isLoading: isLoadingLocal,
    isFetching: isFetchingLocal,
    isError: isLocalError,
    error: localError,
    refetch: refetchLocal,
  } = useLocalActivities(localActivityParams ?? { latitude: 0, longitude: 0 }, localActivityParams !== null);

  const handleOriginSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (originInput.trim().length === 0) return;
    setOriginQuery(originInput.trim());
  };

  const handleTimeSelect = (value: string) => {
    setTimeBucket(value);
    setStep(LOCAL_ADVENTURE_BUCKET_VALUES.has(value) ? 'details' : 'branch');
  };

  const handleBranchSelect = (value: string) => {
    setTravelScope(value);
    setStep('details');
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const toggleGroup = (group: string) => {
    setSelectedGroups((current) =>
      current.includes(group) ? current.filter((item) => item !== group) : [...current, group],
    );
  };

  const handleDetailsSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!origin || !timeBucket) return;

    if (isLocalAdventure) {
      setLocalActivityParams({
        latitude: origin.latitude,
        longitude: origin.longitude,
        originLabel: origin.label,
        groups: selectedGroups.length > 0 ? selectedGroups.join(',') : undefined,
      });
    } else {
      const maxBudget = Number(budgetInput);
      setRecommendationParams({
        maxBudget: budgetInput && !Number.isNaN(maxBudget) ? maxBudget : undefined,
        interests: selectedInterests.length > 0 ? selectedInterests.join(',') : undefined,
        originLat: origin.latitude,
        originLon: origin.longitude,
        timeBucket,
        travelScope: travelScope ?? undefined,
        topN: 10,
      });
    }
    setStep('results');
  };

  const handleStartOver = () => {
    setStep('origin');
    setOriginInput('');
    setOriginQuery(null);
    setTimeBucket(null);
    setTravelScope(null);
    setBudgetInput('');
    setSelectedInterests([]);
    setSelectedGroups(LOCAL_ACTIVITY_GROUPS.map((g) => g.value));
    setRecommendationParams(null);
    setLocalActivityParams(null);
  };

  const handleRefineSearch = () => {
    setStep('details');
  };

  return (
    <section className='finder-panel'>
      <div className='finder-panel__intro'>
        <h2>Plan your adventure</h2>
        <p>Tell us where you're starting from and how much time you have -- we'll narrow it down from there.</p>
      </div>

      {step !== 'results' && <StepIndicator current={step} isLocalAdventure={isLocalAdventure} />}

      {step === 'origin' && (
        <form className='wizard-step' onSubmit={handleOriginSubmit}>
          <h3>Where are you starting from?</h3>
          <div className='finder-grid'>
            <label>
              City or airport
              <input
                type='text'
                placeholder='e.g. Chicago, or JFK airport'
                value={originInput}
                onChange={(event) => setOriginInput(event.target.value)}
              />
            </label>
          </div>

          {isGeocoding && (
            <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
              <span className='spinner' aria-hidden='true' />
              Finding that location…
            </div>
          )}
          {isGeocodeError && !isGeocoding && (
            <div className='status-banner status-banner--error' role='alert'>
              <p>
                {geocodeError instanceof ApiError
                  ? geocodeError.message
                  : "Couldn't find that location. Try a different city or airport name."}
              </p>
            </div>
          )}

          <div className='wizard-nav'>
            <span />
            <button className='button button--primary' type='submit'>
              Continue
            </button>
          </div>
        </form>
      )}

      {step === 'time' && origin && (
        <div className='wizard-step'>
          <div className='origin-summary'>
            Starting from <strong>{origin.label}</strong>
          </div>
          <h3>How much time do you have?</h3>
          <div className='radio-grid'>
            {TIME_BUCKETS.map((bucket) => (
              <label key={bucket.value} className='radio-card'>
                <input
                  type='radio'
                  name='timeBucket'
                  value={bucket.value}
                  checked={timeBucket === bucket.value}
                  onChange={() => handleTimeSelect(bucket.value)}
                />
                <span>{bucket.label}</span>
              </label>
            ))}
          </div>
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={() => setStep('origin')}>
              Back
            </button>
            <span />
          </div>
        </div>
      )}

      {step === 'branch' && origin && (
        <div className='wizard-step'>
          <div className='origin-summary'>
            Starting from <strong>{origin.label}</strong>
          </div>
          <h3>Would you like to stay in your current city or travel somewhere else?</h3>
          <div className='radio-grid'>
            {TRAVEL_SCOPES.map((scope) => (
              <label key={scope.value} className='radio-card'>
                <input
                  type='radio'
                  name='travelScope'
                  value={scope.value}
                  checked={travelScope === scope.value}
                  onChange={() => handleBranchSelect(scope.value)}
                />
                <span>
                  {scope.label}
                  <br />
                  <small>{scope.description}</small>
                </span>
              </label>
            ))}
          </div>
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={() => setStep('time')}>
              Back
            </button>
            <span />
          </div>
        </div>
      )}

      {step === 'details' && origin && timeBucket && isLocalAdventure && (
        <form className='wizard-step' onSubmit={handleDetailsSubmit}>
          <div className='origin-summary'>
            Local adventure near <strong>{origin.label}</strong>
          </div>
          <h3>What are you interested in?</h3>
          <div className='form-row form-row--full'>
            <span className='field-label'>Categories</span>
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
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={() => setStep('time')}>
              Back
            </button>
            <button className='button button--primary' type='submit'>
              Find nearby activities
            </button>
          </div>
        </form>
      )}

      {step === 'details' && origin && timeBucket && !isLocalAdventure && (
        <form className='wizard-step' onSubmit={handleDetailsSubmit}>
          <div className='origin-summary'>
            Starting from <strong>{origin.label}</strong>
          </div>
          <h3>Trip details</h3>
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
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={() => setStep('branch')}>
              Back
            </button>
            <button className='button button--primary' type='submit'>
              Find my trip
            </button>
          </div>
        </form>
      )}

      {step === 'results' && isLocalAdventure && (
        <div className='finder-results'>
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={handleRefineSearch}>
              Refine search
            </button>
            <button className='button button--secondary' type='button' onClick={handleStartOver}>
              Start over
            </button>
          </div>

          {(isLoadingLocal || isFetchingLocal) && (
            <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
              <span className='spinner' aria-hidden='true' />
              Finding nearby activities…
            </div>
          )}

          {isLocalError && !isFetchingLocal && (
            <div className='status-banner status-banner--error' role='alert'>
              <p>{localError instanceof ApiError ? localError.message : 'Something went wrong.'}</p>
              <button className='button button--secondary' type='button' onClick={() => refetchLocal()}>
                Try again
              </button>
            </div>
          )}

          {!isFetchingLocal && !isLocalError && localActivities && (
            <>
              {Object.entries(localActivities.groups).every(([, items]) => items.length === 0) && (
                <p>No nearby activities found in that radius. Try a wider search.</p>
              )}
              {Object.entries(localActivities.groups)
                .filter(([, items]) => items.length > 0)
                .map(([group, items]) => (
                  <div key={group} className='local-activity-group'>
                    <h4>{group.replace(/_/g, ' ')}</h4>
                    <div className='result-grid'>
                      {items.map((activity) => (
                        <article key={`${activity.name}-${activity.latitude}`} className='result-card'>
                          <h4>{activity.name}</h4>
                          {activity.description && <p>{activity.description}</p>}
                          <ul>
                            <li>
                              <strong>Category:</strong> {activity.category.replace(/_/g, ' ')}
                            </li>
                            <li>
                              <strong>Distance:</strong> {activity.distance_km.toFixed(1)} km
                            </li>
                            <li>
                              <strong>Location:</strong> {activity.location}
                            </li>
                          </ul>
                        </article>
                      ))}
                    </div>
                  </div>
                ))}
            </>
          )}
        </div>
      )}

      {step === 'results' && !isLocalAdventure && (
        <div className='finder-results'>
          <div className='wizard-nav'>
            <button className='button button--secondary' type='button' onClick={handleRefineSearch}>
              Refine search
            </button>
            <button className='button button--secondary' type='button' onClick={handleStartOver}>
              Start over
            </button>
          </div>

          {(isLoadingRecs || isFetchingRecs) && (
            <div className='status-banner status-banner--loading' role='status' aria-live='polite'>
              <span className='spinner' aria-hidden='true' />
              Loading recommendations…
            </div>
          )}

          {isRecsError && !isFetchingRecs && (
            <div className='status-banner status-banner--error' role='alert'>
              <p>{recsError instanceof ApiError ? recsError.message : 'Something went wrong loading recommendations.'}</p>
              <button className='button button--secondary' type='button' onClick={() => refetchRecs()}>
                Try again
              </button>
            </div>
          )}

          {!isFetchingRecs && !isRecsError && recommendations && recommendations.length === 0 && (
            <p>No matching trips found within that distance. Try a wider time range or a different scope.</p>
          )}

          {!isFetchingRecs && !isRecsError && recommendations && recommendations.length > 0 && (
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
      )}
    </section>
  );
}
