# tcp-udp-ping

tcp_udp_ping - ping to network hosts in tcp/udp

## Install
require python version `>=2.6` or `>=3.4`

```shell script
pip install -U git+https://github.com/VimT/tcp-udp-ping
```

## Usage

```
Usage: tcp_udp_ping [options] host port

TCP/UDP Ping tool 0.0.7.

Options:
  -h, --help            show this help message and exit
  -u, --udp
  -t, --tcp
  -c COUNT, --count=COUNT
  -i INTERVAL, --interval=INTERVAL
  -W TIMEOUT, --timeout=TIMEOUT
  -6, --ipv6
  -v, --version         show version

  UDP:
    udp options

    -s SIZE, --size=SIZE
```

## Examples
```shell script
# tcp ping to google.com
tcp_udp_ping google.com 80

# udp ping to google.com (udp ping need server return any package) 
tcp_udp_ping -u google.com 80
```
