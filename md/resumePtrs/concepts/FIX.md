## Can you explain what a FIX session is and how it differs from an application message?
* A FIX session is the transport layer that ensures reliable delivery of messages
* Identified by SenderCompID and TargetCompID
* It handles logon, heartbeat, test requests, resends, and logout
* Application messages are the business-level messages
* Like NewOrderSingle (D), ExecutionReport (8), or OrderCancelReplace (G)


## What role do sequence numbers play in a FIX session?
* Every message has a sequence number (MsgSeqNum tag 34)
* Ensures ordering and detects gaps
* If a gap is detected, the counterparty issues a ResendRequest (2) to recover missing messages


## Suppose your FIX engine receives a ResendRequest for 35=8 (ExecutionReports) from seq 105 to 110, but you only have 106–108 stored. How should the engine respond?
* The engine should replay the stored 106–108 with PossDupFlag=Y
* Gap-fill the missing 105, 109, 110 using an Administrative Gap Fill message
* With GapFillFlag=Y


## What’s the purpose of heartbeats and test requests in FIX?
* Heartbeats (35=0) are sent at agreed intervals to confirm connectivity
* If no message is received within the heartbeat interval, the counterparty may send a TestRequest (1)
* If there’s still no response, the session is assumed broken


## Walk me through the FIX message flow for a buy-side sending a new order and receiving a fill.
* Client sends NewOrderSingle (D)
* Broker replies with ExecutionReport (8) with OrdStatus=0 (New)
* When order fills, broker sends another ExecutionReport (8)
* With OrdStatus=2 (Filled) and ExecType=F


## Imagine your FIX engine disconnects right after sending an order. On reconnect, what’s the sequence reset logic?
* During Logon (35=A), the client sends the next expected outbound sequence number
* If sequence mismatch occurs, the counterparty may issue ResendRequest
* Recovery ensures no order is lost
* Duplicate messages are handled via PossDupFlag


## In high-frequency trading, how do you minimize latency in a FIX engine?
* Techniques include using zero-copy parsing
* Pre-allocated buffers
* Lock-free queues
* Batching disk writes for persistence
* Optimizing TCP stack parameters (e.g., disabling Nagle’s algorithm)


## What happens if your engine receives a message with an invalid tag or incorrect checksum?
* The engine should reject it with a Reject (35=3) message
* Including RefTagID and SessionRejectReason
* Depending on the error, it may drop the session if it’s unrecoverable


## How does FIX prevent duplicate fills when replaying messages after recovery?
* Each execution message carries a unique ExecID
* Clients must check for duplicates using this ID
* If the same ExecID is seen again, the client should ignore the fill
* To avoid double booking


## If a buy-side client complains their order never reached the exchange, but you see the NewOrderSingle in your logs, how would you debug?
* I’d check whether the order was acknowledged with an ExecutionReport
* If not, I’d verify sequence numbers
* Check for session-level disconnects at that moment
* Confirm if the message was forwarded to the exchange’s gateway
* Analyze TCP traces to confirm transmission



## Implement a simple FIX message parser in Python that extracts key tags like MsgType (35), SenderCompID (49), and MsgSeqNum (34) from a raw FIX message string.

```python
 def parse_fix_message(message):
     tags = {}
     fields = message.split('|')
     for field in fields:
         if '=' in field:
             tag, value = field.split('=')
             tags[tag] = value
     msg_type = tags.get('35', 'Unknown')
     sender_comp_id = tags.get('49', 'Unknown')
     msg_seq_num = tags.get('34', 'Unknown')
     return {
         'MsgType': msg_type,
         'SenderCompID': sender_comp_id,
         'MsgSeqNum': msg_seq_num
     }
 # Example usage:
 raw_message = "8=FIX.4.2|9=65|35=D|49=Sender|34=1|52=20230816-12:34:56|"
 parsed = parse_fix_message(raw_message)
 print(parsed)  # Output: {'MsgType': 'D', 'SenderCompID': 'Sender', 'MsgSeqNum': '1'}
 ```
 
 ## How to create anki from this markdown file

* mdanki FIX.md FIX_anki.apkg --deck "Collaborated::Interview::SystemConcepts::FIX"


