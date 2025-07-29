## What is Valgrind and what are its primary uses?

* Open-source tool suite for debugging and profiling C/C++ programs
* Detects memory leaks, invalid memory access, and performance issues
* Includes tools like Memcheck for memory errors and Callgrind for profiling
* Used to optimize memory usage and debug errors in systems programming

## What challenges might you face when using Valgrind?

* Significant performance overhead, slowing down execution
* False positives for uninitialized memory due to compiler optimizations
* Requires debugging symbols and suppression files to filter noise
* Not suitable for timing-sensitive applications without adjustments

## What makes RocksDB suitable for high-performance applications?

* High-performance, embeddable key-value store based on LevelDB
* Optimized for low-latency writes and SSD storage
* Uses log-structured merge-tree (LSM) for write-heavy workloads
* Supports compression and tunable options for throughput optimization

## How would you tune RocksDB for a write-heavy workload?

* Increase write buffer size to reduce write amplification
* Enable parallel writes with multiple threads
* Optimize compaction settings (leveled or universal compaction)
* Use bloom filters to reduce read overhead during writes

## What is the architecture of Apache Kafka?

* Distributed streaming platform with publish-subscribe model
* Consists of producers, brokers, and consumers
* Topics partitioned across brokers for scalability
* Partitions are ordered, immutable logs with replication for fault tolerance

## How do you monitor a Kafka cluster in production?

* Track broker health (CPU, memory, disk usage) with Prometheus
* Monitor partition lag and throughput (messages/sec) with Grafana
* Set up alerts for under-replicated partitions or broker failures
* Use JMX metrics to detect consumer group lag

## How does Aeron differ from Kafka?

* High-performance messaging library for low-latency communication
* Uses in-memory, UDP, or shared memory transport, unlike Kafka’s persistent storage
* Ideal for real-time systems like trading, with sub-microsecond latency
* Lacks Kafka’s durability and fault-tolerance features

## What are the advantages of Solace for enterprise messaging?

* Supports multiple protocols (MQTT, AMQP, JMS)
* Offers dynamic routing and robust QoS (guaranteed delivery)
* Scales well in cloud and hybrid environments
* Provides topic-based filtering to reduce network overhead

## What is LBM/Ultra Messaging, and where is it used?

* Latency Busters Messaging (Ultra Messaging) by Informatica
* High-performance, multicast-based messaging for low-latency
* Used in financial systems for market data distribution
* Ensures reliable delivery with minimal jitter

## What is gRPC, and how does it differ from REST?

* High-performance RPC framework using HTTP/2 and Protocol Buffers
* Action-oriented, supports bidirectional streaming, lower latency
* REST is resource-oriented, uses JSON over HTTP/1.1
* gRPC is faster but less interoperable than REST for public APIs

## What is the FIX protocol, and where is it used?

* Financial Information eXchange, standardized for financial messaging
* Text-based, lightweight, supports trade orders and market data
* Used in trading systems for broker-exchange communication
* Includes session management for reliable delivery

## How would you secure a REST API built with a REST SDK?

* Use OAuth 2.0 or JWT for authentication
* Enforce HTTPS for encryption
* Apply rate limiting to prevent abuse
* Validate inputs to avoid injection attacks

## What is staged Event Driven Architecture?

* Design pattern processing events in a specific order
* Uses a single-threaded or sequentially consistent event loop
* Ensures predictable outcomes, avoids race conditions
* Used in systems requiring strict ordering, like trading or workflows

## What are the drawbacks of staged Event Driven Architecture?

* Limited scalability due to staged processing bottlenecks
* Can be slower for high-throughput workloads
* Mitigated by sharding event streams or batching
* Requires careful design to avoid queue


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
* **Example**: Pausing TWAP execution during a price spike and resuming when the market stabilizes to avoid skewed averages

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

## What is Value at Risk (VaR) and its role in financial risk management?
* VaR estimates the maximum potential loss of a portfolio over a time period at a confidence level
* Used to assess market risk, comply with regulations (e.g., Basel III), and set capital requirements
* Methods include historical, parametric, and Monte Carlo simulation
* **Example**: A 95% 1-day VaR of $20,000 means a 5% chance of losing more than $20,000 in a day

## How do you calculate historical VaR with an example?
* Collect historical portfolio returns, sort in ascending order, select the percentile for the confidence level
* Multiply the return at the percentile by the portfolio value
* **Example**: For $1M portfolio, 100 daily returns, 95% confidence, 5th worst return = -1.8%. VaR = $1M × 1.8% = $18,000
* **Challenge**: Ensuring sufficient, clean historical data for accurate estimation

## How do you calculate standard deviation for parametric VaR with an example?
* Compute mean return, calculate variance as average of squared deviations, take square root for standard deviation
* Parametric VaR = Portfolio Value × z-score × Standard Deviation
* **Example**: Returns [-1.5%, 0.8%, -0.3%, 2.1%, -2.0%], mean = -0.18%, std dev ≈ 1.675%. For 95% VaR, $1M × 1.645 × 1.675% ≈ $27,554
* **Challenge**: Assumes normal distribution, which may not hold for extreme market events

## What is limit management and its role in a bank?
* Tracks and enforces risk exposure limits to ensure compliance with regulatory and internal policies
* Covers market risk (e.g., VaR), credit risk, and position limits across asset classes
* Critical for regulatory compliance (e.g., Basel III) and preventing financial losses
* **Example**: A system tracks a $5M VaR limit for a commodities desk, alerting traders at 96% utilization

## How is limit management implemented in a bank’s trading system?
* Uses C++ for high-performance calculations, databases (e.g., MSSQL) for limit storage
* Integrates with FIX for trade data, risk engines for VaR, and reporting for compliance
* Real-time alerts for breaches, with escalation to risk teams
* **Example**: Redesigned C++ components to use MSSQL, improving scalability for multi-asset limit tracking

## What are challenges in implementing limit management systems?
* Ensuring data quality and low-latency processing for real-time monitoring
* Aligning with evolving regulations like Basel III
* Coordinating across business, QA, and RTB teams for delivery



