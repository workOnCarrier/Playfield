## What is TWAP and how is it used in trading?
* Time-Weighted Average Price calculates the average price of a security over a period, weighted by time
* Used in algorithmic trading to execute large orders gradually, minimizing market impact
* Ensures trades align with the market’s average price, avoiding distortions from price spikes
* **Example**: Splitting a large crypto order into smaller trades over an hour to achieve a stable average price

## How do you calculate TWAP with an example?
* Sample prices at regular intervals, sum them, and divide by the number of samples
* For unequal intervals, weight prices by time duration
* **Example**: Prices over 5 minutes: $100.50, $101.00, $100.80, $101.20, $100.90 → TWAP = $504.40 / 5 = $100.88
* **Example with weights**: $50.00 (3 min), $51.00 (4 min), $50.50 (3 min) → TWAP = (150.00 + 204.00 + 151.50) / 10 = $50.55

## What are challenges in implementing a TWAP algorithm?
* Handling missing or irregular price data
* Managing execution during high volatility or low liquidity
* Ensuring minimal market impact while meeting time constraints
* **Example**: Pausing TWAP execution during a price spike and resuming when the market stabilizes to avoid skewed averages