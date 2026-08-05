import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../services/api';

export default function LoginPage() {
  const { login } = useAuth();
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
      await login(email, password);
      navigate('/');
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : 'Could not log in.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className='home-page' id='main-content'>
      <section className='section-card'>
        <h1>Log in</h1>
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
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete='current-password'
              />
            </label>
          </div>
          <div className='finder-actions'>
            <button className='button button--primary' type='submit' disabled={isSubmitting}>
              {isSubmitting ? 'Logging in…' : 'Log in'}
            </button>
          </div>
        </form>

        {errorMessage && (
          <div className='status-banner status-banner--error' role='alert'>
            <p>{errorMessage}</p>
          </div>
        )}

        <p>
          Don't have an account? <Link to='/register'>Register</Link>
        </p>
      </section>
    </main>
  );
}
