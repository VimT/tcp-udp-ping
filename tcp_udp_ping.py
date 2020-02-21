#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import math
import optparse
import random
import signal
import socket
import string
import sys
import time
from timeit import default_timer as timer

__version__ = "0.0.7"


def random_str(length):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


ping_instance = None


class BasePing(object):
    TYPE = ""

    def __init__(self, host, port, num=4, interval=1, is_ipv6=False, timeout=1):
        self.host = host
        self.port = int(port)
        self.num = num
        self.interval = interval
        self.timeout = timeout
        self.is_ipv6 = is_ipv6
        self.received = 0
        self.rtt_list = []
        self.transmitted = 0
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        try:
            self.ip = socket.getaddrinfo(self.host, None, family)[0][4][0]
        except socket.gaierror:
            eprint("error: invalid name or service: '%s'" % self.host)
            exit(1)

    @property
    def loss(self):
        return self.transmitted - self.received

    @property
    def rtt_min(self):
        if not self.rtt_list:
            return 0
        return min(self.rtt_list)

    @property
    def rtt_max(self):
        if not self.rtt_list:
            return 0
        return max(self.rtt_list)

    @property
    def rtt_mean(self):
        if not self.rtt_list:
            return 0
        return sum(self.rtt_list) / len(self.rtt_list)

    @property
    def rtt_mdev(self):
        """平均偏差"""
        if not self.rtt_list:
            return 0
        return math.sqrt(sum([i ** 2 for i in self.rtt_list]) / len(self.rtt_list) - self.rtt_mean ** 2)

    def result(self):
        return {"host": self.host, "port": self.port, "ip": self.ip, "num": self.num, "interval": self.interval,
                "timeout": self.timeout, "is_ipv6": self.is_ipv6, "transmitted": self.transmitted,
                "received": self.received, "loss": self.loss, "rtt_min": self.rtt_min,
                "rtt_max": self.rtt_max, "rtt_mean": self.rtt_mean, "rtt_mdev": self.rtt_mdev}

    def get_socket(self):
        raise NotImplementedError

    def ping(self, s):
        raise NotImplementedError

    def print_result(self):
        print()
        print('--- %s ping statistics ---' % self.TYPE)
        if self.transmitted == 0:
            loss_rate = 0
        else:
            loss_rate = self.loss * 100.0 / self.transmitted
        print('%d packets transmitted, %d received, %.2f%% packet loss' % (
            self.transmitted, self.received, loss_rate))
        if self.received != 0:
            print('rtt min/avg/max/mdev = %.2f/%.2f/%.2f/%.2f ms' % (
                self.rtt_min, self.rtt_mean, self.rtt_max, self.rtt_mdev))

    def print_one(self, seq, rtt):
        name = self.host
        if self.host != self.ip:
            name += " (%s)" % self.ip
        print("Connected to %s[%s]: seq=%d time=%.2f ms" % (name, self.port, seq, rtt))

    def run(self):
        for i in range(self.num):
            s = self.get_socket()
            s_start = timer()
            success = self.ping(s)
            s_stop = timer()
            s_runtime = 1000 * (s_stop - s_start)
            if success:
                self.print_one(i, s_runtime)
                self.received += 1
                self.rtt_list.append(s_runtime)
            self.transmitted += 1
            time.sleep(self.interval)
        self.print_result()


class TCPPing(BasePing):
    TYPE = "TCP"

    def get_socket(self):
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        s = socket.socket(family, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        return s

    def ping(self, s):
        try:
            s.connect((self.host, self.port))
            # wait FIN after buffer flushed
            s.shutdown(socket.SHUT_RD)
            return True
        except socket.timeout:
            print("Connection timed out!")
        except socket.error as e:
            print("socket error:", e)
        except OSError as e:
            print("OS Error:", e)
        return False


class UDPPing(BasePing):
    TYPE = "UDP"

    def __init__(self, host, port, num=4, interval=1, is_ipv6=False, timeout=1, length=50):
        super(UDPPing, self).__init__(host, port, num, interval, is_ipv6, timeout)
        self.length = length

    def get_socket(self):
        family = socket.AF_INET6 if self.is_ipv6 else socket.AF_INET
        s = socket.socket(family, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)
        return s

    def get_payload(self):
        return random_str(self.length).encode()

    def print_one(self, seq, rtt):
        name = self.host
        if self.host != self.ip:
            name += " (%s)" % self.ip
        print("Get %s[%s] reply: seq=%d time=%.2f ms" % (name, self.port, seq, rtt))

    def ping(self, s):
        s.sendto(self.get_payload(), (self.ip, self.port))
        try:
            recv_data, addr = s.recvfrom(65536)
            if addr[0] == self.ip and addr[1] == self.port:
                sys.stdout.flush()
            return True
        except socket.timeout:
            print("Connection timed out!")
        except OSError as e:
            print("OS Error:", e)
        return False


def signal_handler(s, frame):
    """ Catch Ctrl-C and Exit """
    if ping_instance:
        ping_instance.print_result()
    sys.exit(0)


def register_signal():
    # Register SIGINT Handler
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGQUIT, signal_handler)
    except:
        pass


def main():
    register_signal()
    global ping_instance
    usage = "usage: %prog [options] host port"
    parser = optparse.OptionParser(description='TCP/UDP Ping tool %s.' % __version__,
                                   version=__version__, usage=usage)
    parser.remove_option('--version')
    # parser.add_option('host', type=str)
    # parser.add_option('port', type=int, default=80)
    parser.add_option('-u', '--udp', action='store_true')
    parser.add_option('-t', '--tcp', action='store_true')
    parser.add_option('-c', '--count', type=int, default=4)
    parser.add_option('-i', '--interval', type=int, default=1)
    parser.add_option('-W', '--timeout', type=int, default=1)
    parser.add_option('-6', '--ipv6', action='store_true', dest='is_ipv6')
    parser.add_option('-v', '--version', action='version', help='show version')

    udp_parser = parser.add_option_group('UDP', 'udp options')
    udp_parser.add_option('-s', '--size', type=int, default=50)
    args, positional_args = parser.parse_args()
    if len(positional_args) == 0:
        parser.print_help()
        return
    elif len(positional_args) == 1:
        host, = positional_args
        port = 80
    elif len(positional_args) == 2:
        host, port = positional_args
    else:
        host, port = positional_args[:2]
    try:
        port = int(port)
        if port < 0 or port > 65535:
            raise ValueError
    except:
        parser.error("option port: invalid port value: '%s'" % port)

    # print(args, positional_args)
    if not (args.tcp or args.udp):
        args.tcp = True
    if args.tcp:
        ping_instance = TCPPing(host, port, args.count,
                                args.interval, args.is_ipv6, args.timeout)
        ping_instance.run()
    elif args.udp:
        ping_instance = UDPPing(host, port, args.count, args.interval,
                                args.is_ipv6, args.timeout, length=args.size)
        ping_instance.run()
    else:
        print("Nothing happen..")


if __name__ == '__main__':
    main()
