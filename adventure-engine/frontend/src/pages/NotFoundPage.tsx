import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <main className='not-found' id='main-content'>
      <h2>Page not found</h2>
      <p>The requested route does not exist.</p>
      <p>
        <Link to='/'>&larr; Back to home</Link>
      </p>
    </main>
  );
}
