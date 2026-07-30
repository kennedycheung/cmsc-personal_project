import { useState, FormEvent } from 'react';

const interests = [
  'Adventure',
  'Culture',
  'Relaxation',
  'Nature',
  'Food',
  'Wellness',
];

const travelStyles = ['Budget', 'Luxury', 'Family', 'Solo', 'Couples'];

export default function TripPreferenceForm() {
  const [budget, setBudget] = useState('');
  const [location, setLocation] = useState('');
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [travelStyle, setTravelStyle] = useState('Budget');
  const [submitted, setSubmitted] = useState(false);

  const handleInterestToggle = (interest: string) => {
    setSelectedInterests((current) =>
      current.includes(interest)
        ? current.filter((item) => item !== interest)
        : [...current, interest]
    );
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(true);
    console.log({ budget, location, selectedInterests, travelStyle });
  };

  return (
    <section className='preference-panel'>
      <div className='preference-panel__intro'>
        <h2>Tell us about your next trip</h2>
        <p>Set your priorities so the engine can craft better recommendations later.</p>
      </div>

      <form className='preference-form' onSubmit={handleSubmit}>
        <div className='form-row'>
          <label htmlFor='budget'>Budget</label>
          <input
            id='budget'
            type='text'
            placeholder='e.g. $2,000'
            value={budget}
            onChange={(event) => setBudget(event.target.value)}
          />
        </div>

        <div className='form-row'>
          <label htmlFor='location'>Preferred destination</label>
          <input
            id='location'
            type='text'
            placeholder='e.g. Bali, Iceland, Peru'
            value={location}
            onChange={(event) => setLocation(event.target.value)}
          />
        </div>

        <div className='form-row form-row--full'>
          <span className='field-label'>Interests</span>
          <div className='checkbox-grid'>
            {interests.map((interest) => (
              <button
                key={interest}
                type='button'
                aria-pressed={selectedInterests.includes(interest)}
                className={
                  selectedInterests.includes(interest)
                    ? 'chip chip--active'
                    : 'chip'
                }
                onClick={() => handleInterestToggle(interest)}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        <div className='form-row form-row--full'>
          <span className='field-label'>Travel style</span>
          <div className='radio-group'>
            {travelStyles.map((style) => (
              <label key={style} className='radio-card'>
                <input
                  type='radio'
                  name='travelStyle'
                  value={style}
                  checked={travelStyle === style}
                  onChange={() => setTravelStyle(style)}
                />
                <span>{style}</span>
              </label>
            ))}
          </div>
        </div>

        <div className='form-row form-row--actions'>
          <button className='button button--primary' type='submit'>
            Preview preferences
          </button>
        </div>

        {submitted && (
          <div className='submission-summary' role='status' aria-live='polite'>
            <h3>Preview</h3>
            <p>
              Budget: <strong>{budget || 'Not specified'}</strong>
            </p>
            <p>
              Location: <strong>{location || 'Not specified'}</strong>
            </p>
            <p>
              Interests: <strong>{selectedInterests.join(', ') || 'None selected'}</strong>
            </p>
            <p>
              Travel style: <strong>{travelStyle}</strong>
            </p>
            <p className='preference-note'>
              This is a preview only — sign-in and persisted preferences aren't wired up on the frontend yet.
            </p>
          </div>
        )}
      </form>
    </section>
  );
}
