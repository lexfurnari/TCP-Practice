#!/usr/bin/env python3
#
# Author: J. McDonald & A. Furnari
# Date: 04 December 2020
#
# Stop-and-wait client for a simple TCP-like semi-reliable protocol on top of UDP.
#
# What it does: This implements the stop-and-wait protocol, mostly. It sends one UDP packet,
# waits for an ACK, sends one more, waits for an ACK, etc. A sequence number is
# included in each packet, so the server can detect duplicates, detect missing
# packets, and sort any mis-ordered packets back into the correct order. A
# "magic" integer (0xBAADCAFE) is also included with each packet, for no reason
# at all (you can replace it with something else, or remove it entirely).
#
# What it doesn't do: There are no NACKs or timeouts, so if any packet is lost,
# the protocol will deadlock. The ACK numbers are also completely ignored, so if
# there packets get duplicated in the network, things will probably go haywire.
#
# Run the program like this:
#   python3 client_saw.py 1.2.3.4 6000
# This will send data to a UDP server at IP address 1.2.3.4 port 6000.

# Collaboration Log: no collaboration other than with Alexa and Jacob

# Changes to make (for a better protocol):
#       Cope with packet loss, e.g. by having timeouts and retransmitting packets as needed.
#       Cope with packet duplication and mis-ordering, e.g. by using the sequence numbers in ACKs.
#       Use a sliding window for speed, so that multiple packets can be in flight simultaneously.
#       Avoid excessive retransmissions.

import socket
import sys
import time
import struct
import datasource
import trace

# setting verbose = 0 turns off most printing
# setting verbose = 1 turns on a little bit of printing
# setting verbose = 2 turns on a lot of printing
# setting verbose = 3 turns on all printing
verbose = 2

# setting tracefile = None disables writing a trace file for the client
# tracefile = None
tracefile = "client_saw_packets.csv"

magic = 0xBAADCAFE


def main(host, port):
    print("Sending UDP packets to %s:%d" % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Makes a UDP socket!

    trace.init(tracefile,
               "Log of all packets sent and ACKs received by client",
               "SeqNo", "TimeSent", "AckNo", "timeACKed")

    # --------------------------------------------------------------------------------------------------
    # Try getting an ACK - if you can't, then retransmit.
    # If lost (after 3 attempts of retransmitting), then move on and send another packet
    print("Beginning transmission of 10 packets without ACKs...")
    tStart = time.time()
    for seqno in range(0, 180000):
        xpctACKnum = seqno - 10
        # Use a sliding window for speed,
        # so that multiple packets can be in flight simultaneously
        # Goal: Send 10 packets in a row (using current loop?), no waiting for ACKS
        # At this point in code about to send seq# "seqno" and about to receive ACK for seq# "seqno - 10"
        if seqno <= 10:
            print("Sending packet # " + str(seqno) + " without ACK ")
            # get some example data to send
            body = datasource.wait_for_data(seqno)

            # make a header, create a packet, and send it
            hdr = bytearray(struct.pack(">II", magic, seqno))
            pkt = hdr + body
            #tSend = time.time()
            s.sendto(pkt, (host, port))
            if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
                print("Sent packet with seqno %d" % (seqno))
            if xpctACKnum < 0:
                continue

        print("Trying to receive an ACK...")
        try:
            while True:
                s.settimeout(.5)
                print("Timeout of .5 seconds has been set; about to try receiving...")
                (msg, reply_addr) = s.recvfrom(4000)
                print("Waiting for ACK # " + str(xpctACKnum))
                tRecv = time.time()
                # Message received in time, do something with the message...
                # unpack integers from the ACK packet, then print some messages
                (magack, ackno) = struct.unpack(">II", msg)
                # if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
                print("Got ack with seqno %d" % (ackno))
                # write info about the packet and the ACK to the log file
                #trace.write(seqno, tElapsed - tStart, ackno, tRecv - tStart)
                # Cope with packet duplication and mis-ordering, e.g. by using the sequence numbers in ACKs.
                if ackno != xpctACKnum:
                    print(
                        "***UH OH - This is not the ACK we wanted! Receiving again...***")
                    continue
                # optionally retransmit one or more

                # If this is the ACK we want, then stop
                if ackno == xpctACKnum:
                    break

        # If we do not get an ACK back, retransmit!
        except (socket.timeout, socket.error):
            # We never got ACK for xpctACKnum - must retransmit xpctACKnum + 1...etc
            print("*******BEGINNING RETRANSMISSIONS*******")
            for x in range(xpctACKnum, seqno):
                print("Beginning retransmission of packet # " + str(x))
                # get some example data to send
                body = datasource.wait_for_data(x)
                # make a header, create a packet, and send it
                hdr = bytearray(struct.pack(">II", magic, x))
                pkt = hdr + body
                s.sendto(pkt, (host, port))
                print("Sent retransmission of packet # " + str(x))
                if verbose >= 3 or (verbose >= 1 and x < 5 or x % 1000 == 0):
                    print("Sent packet with seqno %d" % (x))
                    
        # At this point either an ACK has been received OR
        # The three retransmissions have failed. In either case,
        # send the next packet
# ---------------------------------------------------------------------------------------------------
    end = time.time()
    elapsed = end - tStart
    print("Finished sending all packets!")
    print("Elapsed time: %0.4f s" % (elapsed))
    trace.close()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("To send data to the server at 1.2.3.4 port 6000, try running:")
        print("   python3 %s 1.2.3.4 6000" % (sys.argv[0]))
        sys.exit(0)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
