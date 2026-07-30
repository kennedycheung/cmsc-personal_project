import { Routes, Route, Link } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import DestinationPage from '../pages/DestinationPage';
import NotFoundPage from '../pages/NotFoundPage';

export default function AppRoutes() {
  return (
    <div>
      <a href='#main-content' className='skip-link'>
        Skip to main content
      </a>
      <header className='app-header'>
        <Link to='/' className='brand'>Adventure Arbitrage Engine</Link>
      </header>
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='/destinations/:id' element={<DestinationPage />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
