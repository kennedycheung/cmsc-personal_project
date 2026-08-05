import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../services/api';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await register(email, password);
      navigate('/');
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : 'Could not register.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className='home-page' id='main-content'>
      <section className='section-card'>
        <h1>Create an account</h1>
        <form className='finder-form' onSubmit={handleSubmit}>
          <div className='finder-grid'>
            <label>
              Email
              <input
                type='email'
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete='email'
              />
            </label>
            <label>
              Password
              <input
                type='password'
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete='new-password'
              />
            </label>
          </div>
          <div className='finder-actions'>
            <button className='button button--primary' type='submit' disabled={isSubmitting}>
              {isSubmitting ? 'Creating account…' : 'Register'}
            </button>
          </div>
        </form>

        {errorMessage && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>{errorMessage}</p>
          </div>
        )}

        <p>
          Already have an account? <Link to='/login'>Log in</Link>
        </p>
      </section>
    </main>
  );
}
