import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import BudgetCalculator from './BudgetCalculator';

describe('BudgetCalculator', () => {
  it('computes total cost, cost per day, and budget remaining from user input', async () => {
    const user = userEvent.setup();
    render(<BudgetCalculator />);

    await user.type(screen.getByLabelText(/trip budget/i), '2000');
    await user.type(screen.getByLabelText(/trip duration/i), '10');
    await user.type(screen.getByLabelText(/transportation cost/i), '500');
    await user.type(screen.getByLabelText(/lodging cost/i), '800');
    await user.type(screen.getByLabelText(/food estimate/i), '400');
    await user.type(screen.getByLabelText(/activity costs/i), '100');

    // total = 500 + 800 + 400 + 100 = 1800
    expect(screen.getByText('$1,800.00')).toBeInTheDocument();
    // cost per day = 1800 / 10 = 180
    expect(screen.getByText('$180.00')).toBeInTheDocument();
    // remaining = 2000 - 1800 = 200
    expect(screen.getByText('$200.00')).toBeInTheDocument();
  });

  it('prompts for duration/budget before showing derived figures', () => {
    render(<BudgetCalculator />);
    expect(screen.getByText(/enter trip duration/i)).toBeInTheDocument();
    expect(screen.getByText(/enter budget/i)).toBeInTheDocument();
  });
});
