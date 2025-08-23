## What is TWAP (Time-Weighted Average Price), and where is it used?

* TWAP is the average price of an asset over a defined period, weighted by the time each price was active.
* Used as a trading benchmark and order execution algorithm to minimize market impact.
* Commonly implemented in trading systems to break large orders into smaller trades at regular intervals, reducing price slippage and signaling.

## What are the key steps to calculate TWAP?

* Specify the time interval to measure prices (e.g., every minute, hour, day).
* Record the price at each selected timepoint.
* Apply the formula:  
  $$\text{TWAP} = \frac{\sum_{j}{P_{j} \cdot T_{j}}}{\sum_{j}{T_{j}}}$$  
  Where $$P_j$$ is the asset price at time $$j$$, $$T_j$$ is the duration between measurements.
* For most practical cases, with equal time intervals:  
  $$\text{TWAP} = \frac{P_1 + P_2 + ... + P_n}{n}$$.

## What is the difference between TWAP and VWAP?

* VWAP (Volume-Weighted Average Price) weights each price by the volume traded, whereas TWAP uses only timeweighting—ignoring volume.
* TWAP is predictable and volume-independent; VWAP adapts execution to trading volume.
* TWAP is preferred when evenly timed trades are desired; VWAP for volume-sensitive strategies.

## Why do traders and algorithms use TWAP?

* To minimize market impact of large orders by breaking them up over time.
* To achieve execution at the market price average, improving fill prices and reducing slippage.
* Avoids signaling large orders to the market, reducing likelihood of being front-run.

## Python sample: How to calculate TWAP for asset prices?

```python
import pandas as pd

# Example price data (simulate minute-by-minute prices)
prices = [100.5, 101.0, 100.8, 101.5, 101.2]

# Calculate TWAP -- equal time intervals assumed
twap = sum(prices) / len(prices)
print("TWAP:", twap)

# For a DataFrame with 'price' and custom time intervals
df = pd.DataFrame({'price': [100.5, 101.0, 100.8, 101.5, 101.2],
                   'duration': [1,  # durations in minutes
twap_weighted = (df['price'] * df['duration']).sum() / df['duration'].sum()
print("Weighted TWAP:", twap_weighted)

```


## How to create anki from this markdown file

* mdanki twap_price_anki.md twap_price_anki.apkg --deck "Collaborated::CodeInterview::Domain::TwapPriceCalculation"

