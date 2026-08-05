import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import DestinationPage from '../pages/DestinationPage';
import DiscoverPage from '../pages/DiscoverPage';
import AdventuresPage from '../pages/AdventuresPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import NotFoundPage from '../pages/NotFoundPage';
import { useAuth } from '../hooks/useAuth';

function AuthNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (user) {
    return (
      <>
        <span>{user.email}</span>
        <button
          type='button'
          className='app-nav-logout'
          onClick={() => {
            logout();
            navigate('/');
          }}
        >
          Log out
        </button>
      </>
    );
  }

  return (
    <>
      <Link to='/login'>Log in</Link>
      <Link to='/register'>Register</Link>
    </>
  );
}

export default function AppRoutes() {
  return (
    <div>
      <a href='#main-content' className='skip-link'>
        Skip to main content
      </a>
      <header className='app-header'>
        <Link to='/' className='brand'>Adventure Arbitrage Engine</Link>
        <nav className='app-nav'>
          <Link to='/adventures'>Adventures</Link>
          <Link to='/discover'>Discover</Link>
          <AuthNav />
        </nav>
      </header>
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='/destinations/:id' element={<DestinationPage />} />
        <Route path='/adventures' element={<AdventuresPage />} />
        <Route path='/discover' element={<DiscoverPage />} />
        <Route path='/login' element={<LoginPage />} />
        <Route path='/register' element={<RegisterPage />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
