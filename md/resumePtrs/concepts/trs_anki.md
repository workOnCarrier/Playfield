## What is a Total Return Swap (TRS) and its role in financial markets?
* A derivative where one party pays the total return (price changes + income) of an asset, and the other pays a fixed/floating rate
* Used for gaining asset exposure without ownership, hedging, or risk management
* Common in commodities, equities, and credit markets
* **Example**: A hedge fund gains exposure to a stock’s returns without owning it, paying SOFR + 2% to a bank

## How do you calculate TRS financial flows with an example?
* Total return = Price appreciation/depreciation + Income (e.g., dividends)
* Fixed leg = Notional × (Interest rate + Spread)
* **Example**: $1M notional, stock price rises from $100 to $110, $1/share dividend. Total return = $110,000. Hedge fund pays $50,000 (SOFR + 2%), receives $60,000 net.
* **Alternative**: If stock falls to $90, total return = -$90,000. Hedge fund pays $140,000 net (fixed leg + loss).

## What are challenges in implementing TRS in a risk system?
* Modeling accurate total return calculations for volatile assets
* Handling counterparty credit risk and collateral requirements
* Integrating with existing risk pipelines for real-time exposure tracking
* **Example**: Adding TRS cash flows to a C++ risk engine, stress-testing for commodity price drops to meet Basel III requirements