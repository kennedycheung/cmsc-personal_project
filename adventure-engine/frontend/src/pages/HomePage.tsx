import AdventureFinder from '../components/AdventureFinder';
import BudgetCalculator from '../components/BudgetCalculator';
import TripPreferenceForm from '../components/TripPreferenceForm';

export default function HomePage() {
  return (
    <main className='home-page' id='main-content'>
      <section className='hero'>
        <div className='hero__copy'>
          <h1>Adventure Arbitrage Engine</h1>
          <p>
            Discover better trips with budget planning, destination suggestions, and preference-based recommendations.
          </p>
        </div>
      </section>

      <AdventureFinder />
      <BudgetCalculator />
      <TripPreferenceForm />
    </main>
  );
}
