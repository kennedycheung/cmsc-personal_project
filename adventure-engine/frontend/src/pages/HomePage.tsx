import AdventureWizard from '../components/AdventureWizard';

export default function HomePage() {
  return (
    <main className='home-page' id='main-content'>
      <section className='hero'>
        <div className='hero__copy'>
          <h1>Adventure Arbitrage Engine</h1>
          <p>
            Start from where you are and how much time you have -- we'll narrow it down to the most memorable
            adventure you can realistically have.
          </p>
        </div>
      </section>

      <AdventureWizard />
    </main>
  );
}
