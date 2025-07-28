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

## What is Sequential Event Driven Architecture?

* Design pattern processing events in a specific order
* Uses a single-threaded or sequentially consistent event loop
* Ensures predictable outcomes, avoids race conditions
* Used in systems requiring strict ordering, like trading or workflows

## What are the drawbacks of Sequential Event Driven Architecture?

* Limited scalability due to sequential processing bottlenecks
* Can be slower for high-throughput workloads
* Mitigated by sharding event streams or batching
* Requires careful design to avoid queue