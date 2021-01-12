Experiments with reliable transport over UDP: 

We added TCP like protocols to better_client.py and deployed the client and server code on Amazon 
Cloud Machines. Some of the servers had issues such as delayed sending, dropped data and out of order 
sending. We implmeneted a sliding window protocol to improve the speed and timeouts to handle lost and delayed data. 
If the packets were not received, those packets were retransmitted. Our code does not handle out of order packets. 
All packets are received, however,changes to the server code were not made to rearrange the packets as they came in. 

* datasource.py - Python code to generate example data packets.
* better_client.py - improved test_client.py --> faster, retransmits, no lost data. 
* test_client.py - a bare-bones stop-and-wait protocol client. 
* server.py - A server that receives and ACKs packets.
* datasink.py - Python code to consume and analyze arriving packets.
* trace.py - Python code to log packet times and sequence numbers.
