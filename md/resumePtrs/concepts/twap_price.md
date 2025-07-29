### What is TWAP Price Calculation?

**Time-Weighted Average Price (TWAP)** is a trading metric used to calculate the average price of a security over a specified period, weighted by time. It’s commonly used in financial markets, particularly in algorithmic trading, to execute large orders gradually and minimize market impact. TWAP ensures that trades are executed at an average price reflective of the market over time, avoiding distortions from sudden price spikes.

- **Explanation**: TWAP is calculated by taking price samples at regular intervals (e.g., every minute) over a time period, summing these prices, and dividing by the number of samples. It’s useful for executing trades in a way that aligns with the market’s average price, especially for illiquid assets or large orders.
- **Applied Example**: In a trading system, TWAP is used to execute a large buy order for a cryptocurrency by splitting it into smaller orders executed at regular intervals, ensuring the average purchase price reflects the market’s behavior over the trading period.

### Sample TWAP Calculation

Let’s calculate the TWAP for a stock over a 5-minute period, with price samples taken every minute.

**Scenario**:
- Stock prices recorded every minute:  
  - Minute 1: $100.50  
  - Minute 2: $101.00  
  - Minute 3: $100.80  
  - Minute 4: $101.20  
  - Minute 5: $100.90  

**Step-by-Step Calculation**:
1. **List the prices**: $100.50, $101.00, $100.80, $101.20, $100.90
2. **Sum the prices**:  
   $100.50 + $101.00 + $100.80 + $101.20 + $100.90 = $504.40
3. **Count the samples**: 5 (one per minute)
4. **Calculate TWAP**:  
   TWAP = Total Sum of Prices / Number of Samples = $504.40 / 5 = $100.88

**Result**: The TWAP price for the stock over this 5-minute period is **$100.88**.

### Another Example with Unequal Intervals

If sampling intervals are not uniform (e.g., due to missing data), TWAP can be weighted by the time each price represents.

**Scenario**:
- Stock prices over 10 minutes:  
  - Minute 1–3 (3 minutes): $50.00  
  - Minute 4–7 (4 minutes): $51.00  
  - Minute 8–10 (3 minutes): $50.50  

**Step-by-Step Calculation**:
1. **Weight each price by time duration**:  
   - $50.00 × 3 minutes = 150.00  
   - $51.00 × 4 minutes = 204.00  
   - $50.50 × 3 minutes = 151.50  
2. **Sum the weighted prices**:  
   150.00 + 204.00 + 151.50 = 505.50  
3. **Sum the time durations**:  
   3 + 4 + 3 = 10 minutes  
4. **Calculate TWAP**:  
   TWAP = Total Weighted Sum / Total Time = 505.50 / 10 = $50.55

**Result**: The TWAP price is **$50.55**.

### Mock Interview Question
- **Question**: How would you implement a TWAP algorithm in a trading system to execute a large order over an hour?
- **Answer**: I’d design an algorithm to divide the order into smaller chunks executed at fixed intervals (e.g., every minute). For each interval, I’d sample the current market price, execute a portion of the order, and track the prices. At the end, I’d calculate the TWAP by averaging the sampled prices. To handle volatility, I’d add logic to pause execution during extreme price spikes, resuming when the market stabilizes.

### Markdown for Anki (mdanki Format)



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

