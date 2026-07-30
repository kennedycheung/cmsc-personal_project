import { useMemo, useState } from 'react';

export default function BudgetCalculator() {
  const [transportation, setTransportation] = useState('');
  const [lodging, setLodging] = useState('');
  const [food, setFood] = useState('');
  const [activities, setActivities] = useState('');
  const [budget, setBudget] = useState('');
  const [duration, setDuration] = useState('');

  const formatCurrency = (value: number) =>
    value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

  const transportationValue = Number(transportation) || 0;
  const lodgingValue = Number(lodging) || 0;
  const foodValue = Number(food) || 0;
  const activitiesValue = Number(activities) || 0;
  const budgetValue = Number(budget) || 0;
  const durationValue = Number(duration) || 0;

  const totalCost = useMemo(
    () => transportationValue + lodgingValue + foodValue + activitiesValue,
    [transportationValue, lodgingValue, foodValue, activitiesValue],
  );

  const costPerDay = useMemo(
    () => (durationValue > 0 ? totalCost / durationValue : 0),
    [totalCost, durationValue],
  );

  const budgetRemaining = useMemo(
    () => (budgetValue > 0 ? budgetValue - totalCost : 0),
    [budgetValue, totalCost],
  );

  return (
    <section className='budget-panel'>
      <div className='budget-panel__intro'>
        <h2>Travel Budget Calculator</h2>
        <p>Estimate your trip cost and compare it to your budget.</p>
      </div>

      <div className='budget-form'>
        <div className='budget-form__grid'>
          <label>
            Trip budget
            <input
              type='number'
              min='0'
              placeholder='Enter your budget'
              value={budget}
              onChange={(event) => setBudget(event.target.value)}
            />
          </label>

          <label>
            Trip duration (days)
            <input
              type='number'
              min='1'
              placeholder='Number of days'
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
            />
          </label>

          <label>
            Transportation cost
            <input
              type='number'
              min='0'
              placeholder='e.g. 500'
              value={transportation}
              onChange={(event) => setTransportation(event.target.value)}
            />
          </label>

          <label>
            Lodging cost
            <input
              type='number'
              min='0'
              placeholder='e.g. 1200'
              value={lodging}
              onChange={(event) => setLodging(event.target.value)}
            />
          </label>

          <label>
            Food estimate
            <input
              type='number'
              min='0'
              placeholder='e.g. 400'
              value={food}
              onChange={(event) => setFood(event.target.value)}
            />
          </label>

          <label>
            Activity costs
            <input
              type='number'
              min='0'
              placeholder='e.g. 250'
              value={activities}
              onChange={(event) => setActivities(event.target.value)}
            />
          </label>
        </div>

        <div className='budget-summary'>
          <div>
            <span>Total trip cost</span>
            <strong>{formatCurrency(totalCost)}</strong>
          </div>
          <div>
            <span>Cost per day</span>
            <strong>
              {durationValue > 0 ? formatCurrency(costPerDay) : 'Enter trip duration'}
            </strong>
          </div>
          <div>
            <span>Budget remaining</span>
            <strong>
              {budgetValue > 0 ? formatCurrency(budgetRemaining) : 'Enter budget'}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}
