# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: t -*-
# vi: set ft=python sts=4 ts=4 sw=4 noet :

# This file is part of Fail2Ban.
#
# Fail2Ban is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fail2Ban is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fail2Ban; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

__author__ = "Fail2Ban Developers, Alexander Koeppe, Serg G. Brester, Yaroslav Halchenko"
__copyright__ = "Copyright (c) 2004-2016 Fail2ban Developers"
__license__ = "GPL"

import socket
import struct
import os
import re

from .utils import Utils
from ..helpers import getLogger, MyTime, splitwords

# Gets the instance of the logger.
logSys = getLogger(__name__)


##
# Helper functions
#
#
def asip(ip):
	"""A little helper to guarantee ip being an IPAddr instance"""
	if isinstance(ip, IPAddr):
		return ip
	return IPAddr(ip)

def getfqdn(name=''):
	"""Get fully-qualified hostname of given host, thereby resolve of an external
	IPs and name will be preferred before the local domain (or a loopback), see gh-2438
	"""
	try:
		name = name or socket.gethostname()
		names = (
			ai[3] for ai in socket.getaddrinfo(
				name, None, 0, socket.SOCK_DGRAM, 0, socket.AI_CANONNAME
			) if ai[3]
		)
		if names:
			# first try to find a fqdn starting with the host name like www.domain.tld for www:
			pref = name+'.'
			first = None
			for ai in names:
				if ai.startswith(pref):
					return ai
				if not first: first = ai
			# not found - simply use first known fqdn:
			return first
	except socket.error:
		pass
	# fallback to python's own getfqdn routine:
	return socket.getfqdn(name)


##
# Utils class for DNS handling.
#
# This class contains only static methods used to handle DNS 
#
class DNSUtils:

	# todo: make configurable the expired time and max count of cache entries:
	CACHE_nameToIp = Utils.Cache(maxCount=1000, maxTime=5*60)
	CACHE_ipToName = Utils.Cache(maxCount=1000, maxTime=5*60)
	# static cache used to hold sets read from files:
	CACHE_fileToIp = Utils.Cache(maxCount=100, maxTime=5*60)

	@staticmethod
	def dnsToIp(dns):
		""" Convert a DNS into an IP address using the Python socket module.
			Thanks to Kevin Drapel.
		"""
		# cache, also prevent long wait during retrieving of ip for wrong dns or lazy dns-system:
		ips = DNSUtils.CACHE_nameToIp.get(dns)
		if ips is not None: 
			return ips
		# retrieve ips
		ips = set()
		saveerr = None
		for fam in ((socket.AF_INET,socket.AF_INET6) if DNSUtils.IPv6IsAllowed() else (socket.AF_INET,)):
			try:
				for result in socket.getaddrinfo(dns, None, fam, 0, socket.IPPROTO_TCP):
					# if getaddrinfo returns something unexpected:
					if len(result) < 4 or not len(result[4]): continue
					# get ip from `(2, 1, 6, '', ('127.0.0.1', 0))`,be sure we've an ip-string
					# (some python-versions resp. host configurations causes returning of integer there):
					ip = IPAddr(str(result[4][0]), IPAddr._AF2FAM(fam))
					if ip.isValid:
						ips.add(ip)
			except Exception as e:
				saveerr = e
		if not ips and saveerr:
			logSys.warning("Unable to find a corresponding IP address for %s: %s", dns, saveerr)

		DNSUtils.CACHE_nameToIp.set(dns, ips)
		return ips

	@staticmethod
	def ipToName(ip):
		# cache, also prevent long wait during retrieving of name for wrong addresses, lazy dns:
		v = DNSUtils.CACHE_ipToName.get(ip, ())
		if v != ():
			return v
		# retrieve name
		try:
			v = socket.gethostbyaddr(ip)[0]
		except socket.error as e:
			logSys.debug("Unable to find a name for the IP %s: %s", ip, e)
			v = None
		DNSUtils.CACHE_ipToName.set(ip, v)
		return v

	@staticmethod
	def textToIp(text, useDns):
		""" Return the IP of DNS found in a given text.
		"""
		ipList = set()
		# Search for plain IP
		plainIP = IPAddr.searchIP(text)
		if plainIP is not None:
			ip = IPAddr(plainIP)
			if ip.isValid:
				ipList.add(ip)

		# If we are allowed to resolve -- give it a try if nothing was found
		if useDns in ("yes", "warn") and not ipList:
			# Try to get IP from possible DNS
			ip = DNSUtils.dnsToIp(text)
			ipList.update(ip)
			if ip and useDns == "warn":
				logSys.warning("Determined IP using DNS Lookup: %s = %s",
					text, ipList)

		return ipList

	@staticmethod
	def getHostname(fqdn=True):
		"""Get short hostname or fully-qualified hostname of host self"""
		# try find cached own hostnames (this tuple-key cannot be used elsewhere):
		key = ('self','hostname', fqdn)
		name = DNSUtils.CACHE_ipToName.get(key)
		if name is not None:
			return name
		# get it using different ways (hostname, fully-qualified or vice versa):
		name = ''
		for hostname in (
			(getfqdn, socket.gethostname) if fqdn else (socket.gethostname, getfqdn)
		):
			try:
				name = hostname()
				break
			except Exception as e: # pragma: no cover
				logSys.warning("Retrieving own hostnames failed: %s", e)
		# cache and return :
		DNSUtils.CACHE_ipToName.set(key, name)
		return name

	# key find cached own hostnames (this tuple-key cannot be used elsewhere):
	_getSelfNames_key = ('self','dns')

	@staticmethod
	def getSelfNames():
		"""Get own host names of self"""
		# try find cached own hostnames:
		names = DNSUtils.CACHE_ipToName.get(DNSUtils._getSelfNames_key)
		if names is not None:
			return names
		# get it using different ways (a set with names of localhost, hostname, fully qualified):
		names = set([
			'localhost', DNSUtils.getHostname(False), DNSUtils.getHostname(True)
		]) - set(['']) # getHostname can return ''
		# cache and return :
		DNSUtils.CACHE_ipToName.set(DNSUtils._getSelfNames_key, names)
		return names

	# key to find cached network interfaces IPs (this tuple-key cannot be used elsewhere):
	_getNetIntrfIPs_key = ('netintrf','ips')

	@staticmethod
	def getNetIntrfIPs():
		"""Get own IP addresses of self"""
		# to find cached own IPs:
		ips = DNSUtils.CACHE_nameToIp.get(DNSUtils._getNetIntrfIPs_key)
		if ips is not None:
			return ips
		# try to obtain from network interfaces if possible (implemented for this platform):
		try:
			ips = IPAddrSet([a for ni, a in DNSUtils._NetworkInterfacesAddrs()])
		except:
			ips = IPAddrSet()
		# cache and return :
		DNSUtils.CACHE_nameToIp.set(DNSUtils._getNetIntrfIPs_key, ips)
		return ips

	# key to find cached own IPs (this tuple-key cannot be used elsewhere):
	_getSelfIPs_key = ('self','ips')

	@staticmethod
	def getSelfIPs():
		"""Get own IP addresses of self"""
		# to find cached own IPs:
		ips = DNSUtils.CACHE_nameToIp.get(DNSUtils._getSelfIPs_key)
		if ips is not None:
			return ips
		# firstly try to obtain from network interfaces if possible (implemented for this platform):
		ips = IPAddrSet(DNSUtils.getNetIntrfIPs())
		# extend it using different ways (a set with IPs of localhost, hostname, fully qualified):
		for hostname in DNSUtils.getSelfNames():
			try:
				ips |= IPAddrSet(DNSUtils.dnsToIp(hostname))
			except Exception as e: # pragma: no cover
				logSys.warning("Retrieving own IPs of %s failed: %s", hostname, e)
		# cache and return :
		DNSUtils.CACHE_nameToIp.set(DNSUtils._getSelfIPs_key, ips)
		return ips

	@staticmethod
	def getIPsFromFile(fileName, noError=True):
		"""Get set of IP addresses or subnets from file"""
		# to find cached IPs:
		ips = DNSUtils.CACHE_fileToIp.get(fileName)
		if ips is not None:
			return ips
		# try to obtain set from file:
		ips = FileIPAddrSet(fileName)
		#ips.load() - load on demand
		# cache and return :
		DNSUtils.CACHE_fileToIp.set(fileName, ips)
		return ips

	_IPv6IsAllowed = None

	@staticmethod
	def _IPv6IsSupportedBySystem():
		if not socket.has_ipv6:
			return False
		# try to check sysctl net.ipv6.conf.all.disable_ipv6:
		try:
			with open('/proc/sys/net/ipv6/conf/all/disable_ipv6', 'rb') as f:
				# if 1 - disabled, 0 - enabled
				return not int(f.read())
		except:
			pass
		s = None
		try:
			# try to create INET6 socket:
			s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
			# bind it to free port for any interface supporting IPv6:
			s.bind(("", 0));
			return True
		except Exception as e: # pragma: no cover
			if hasattr(e, 'errno'):
				import errno
				# negative (-9 'Address family not supported', etc) or not available/supported:
				if e.errno < 0 or e.errno in (errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT):
					return False
				# in use:
				if e.errno in (errno.EADDRINUSE, errno.EACCES): # normally unreachable (free port and root)
					return True
		finally:
			if s: s.close()
		# unable to detect:
		return None

	@staticmethod
	def setIPv6IsAllowed(value):
		DNSUtils._IPv6IsAllowed = value
		logSys.debug("IPv6 is %s", ('on' if value else 'off') if value is not None else 'auto')
		return value

	# key to find cached value of IPv6 allowance (this tuple-key cannot be used elsewhere):
	_IPv6IsAllowed_key = ('self','ipv6-allowed')

	@staticmethod
	def IPv6IsAllowed():
		if DNSUtils._IPv6IsAllowed is not None:
			return DNSUtils._IPv6IsAllowed
		v = DNSUtils.CACHE_nameToIp.get(DNSUtils._IPv6IsAllowed_key)
		if v is not None:
			return v
		v = DNSUtils._IPv6IsSupportedBySystem()
		if v is None:
			# detect by IPs of host:
			ips = DNSUtils.getNetIntrfIPs()
			if not ips:
				DNSUtils._IPv6IsAllowed = True; # avoid self recursion from getSelfIPs -> dnsToIp -> IPv6IsAllowed
				try:
					ips = DNSUtils.getSelfIPs()
				finally:
					DNSUtils._IPv6IsAllowed = None
			v = any((':' in ip.ntoa) for ip in ips)
		DNSUtils.CACHE_nameToIp.set(DNSUtils._IPv6IsAllowed_key, v)
		return v


##
# Class for IP address handling.
#
# This class contains methods for handling IPv4 and IPv6 addresses.
#
class IPAddr(object):
	"""Encapsulate functionality for IPv4 and IPv6 addresses
	"""

	IP_4_RE = r"""(?:\d{1,3}\.){3}\d{1,3}"""
	IP_6_RE = r"""(?:[0-9a-fA-F]{1,4}::?|:){1,7}(?:[0-9a-fA-F]{1,4}|(?<=:):)"""
	IP_4_6_CRE = re.compile(
	  r"""^(?:(?P<IPv4>%s)|\[?(?P<IPv6>%s)\]?)$""" % (IP_4_RE, IP_6_RE))
	IP_W_CIDR_CRE = re.compile(
	  r"""^(%s|%s)/(?:(\d+)|(%s|%s))$""" % (IP_4_RE, IP_6_RE, IP_4_RE, IP_6_RE))
	# An IPv4 compatible IPv6 to be reused (see below)
	IP6_4COMPAT = None

	# object attributes
	__slots__ = '_family','_addr','_plen','_maskplen','_raw'

	# todo: make configurable the expired time and max count of cache entries:
	CACHE_OBJ = Utils.Cache(maxCount=10000, maxTime=5*60)

	CIDR_RAW = -2
	CIDR_UNSPEC = -1
	FAM_IPv4 = CIDR_RAW - socket.AF_INET
	FAM_IPv6 = CIDR_RAW - socket.AF_INET6
	@staticmethod
	def _AF2FAM(v):
		return IPAddr.CIDR_RAW - v

	def __new__(cls, ipstr, cidr=CIDR_UNSPEC):
		if cidr == IPAddr.CIDR_UNSPEC and isinstance(ipstr, (tuple, list)):
			cidr = IPAddr.CIDR_RAW
		if cidr == IPAddr.CIDR_RAW: # don't cache raw
			ip = super(IPAddr, cls).__new__(cls)
			ip.__init(ipstr, cidr)
			return ip
		# check already cached as IPAddr
		args = (ipstr, cidr)
		ip = IPAddr.CACHE_OBJ.get(args)
		if ip is not None:
			return ip
		# wrap mask to cidr (correct plen):
		if cidr == IPAddr.CIDR_UNSPEC:
			ipstr, cidr = IPAddr.__wrap_ipstr(ipstr)
			args = (ipstr, cidr)
			# check cache again:
			if cidr != IPAddr.CIDR_UNSPEC:
				ip = IPAddr.CACHE_OBJ.get(args)
				if ip is not None:
					return ip
		ip = super(IPAddr, cls).__new__(cls)
		ip.__init(ipstr, cidr)
		if ip._family != IPAddr.CIDR_RAW:
			IPAddr.CACHE_OBJ.set(args, ip)
		return ip

	@staticmethod
	def __wrap_ipstr(ipstr):
		# because of standard spelling of IPv6 (with port) enclosed in brackets ([ipv6]:port),
		# remove they now (be sure the <HOST> inside failregex uses this for IPv6 (has \[?...\]?)
		if len(ipstr) > 2 and ipstr[0] == '[' and ipstr[-1] == ']':
			ipstr = ipstr[1:-1]
		# test mask:
		if "/" not in ipstr:
			return ipstr, IPAddr.CIDR_UNSPEC
		s = IPAddr.IP_W_CIDR_CRE.match(ipstr)
		if s is None:
			return ipstr, IPAddr.CIDR_UNSPEC
		s = list(s.groups())
		if s[2]: # 255.255.255.0 resp. ffff:: style mask
			s[1] = IPAddr.masktoplen(s[2])
		del s[2]
		try:
			s[1] = int(s[1])
		except ValueError:
			return ipstr, IPAddr.CIDR_UNSPEC
		return s
		
	def __init(self, ipstr, cidr=CIDR_UNSPEC):
		""" initialize IP object by converting IP address string
			to binary to integer
		"""
		self._family = socket.AF_UNSPEC
		self._addr = 0
		self._plen = 0
		self._maskplen = None
		# always save raw value (normally used if really raw or not valid only):
		self._raw = ipstr
		# if not raw - recognize family, set addr, etc.:
		if cidr != IPAddr.CIDR_RAW:
			if cidr is not None and cidr < IPAddr.CIDR_RAW:
				family = [IPAddr.CIDR_RAW - cidr]
			else:
				family = [socket.AF_INET, socket.AF_INET6]
			for family in family:
				try:
					binary = socket.inet_pton(family, ipstr)
					self._family = family
					break
				except socket.error:
					continue

			if self._family == socket.AF_INET:
				# convert host to network byte order
				self._addr, = struct.unpack("!L", binary)
				self._plen = 32

				# mask out host portion if prefix length is supplied
				if cidr is not None and cidr >= 0:
					mask = ~(0xFFFFFFFF >> cidr)
					self._addr &= mask
					self._plen = cidr

			elif self._family == socket.AF_INET6:
				# convert host to network byte order
				hi, lo = struct.unpack("!QQ", binary)
				self._addr = (hi << 64) | lo
				self._plen = 128

				# mask out host portion if prefix length is supplied
				if cidr is not None and cidr >= 0:
					mask = ~(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF >> cidr)
					self._addr &= mask
					self._plen = cidr

				# if IPv6 address is a IPv4-compatible, make instance a IPv4
				elif self.isInNet(IPAddr.IP6_4COMPAT):
					self._addr = lo & 0xFFFFFFFF
					self._family = socket.AF_INET
					self._plen = 32
		else:
			self._family = IPAddr.CIDR_RAW

	def __repr__(self):
		return repr(self.ntoa)

	def __str__(self):
		return self.ntoa if isinstance(self.ntoa, str) else str(self.ntoa)

	def __reduce__(self):
		"""IPAddr pickle-handler, that simply wraps IPAddr to the str

		Returns a string as instance to be pickled, because fail2ban-client can't
		unserialize IPAddr objects
		"""
		return (str, (self.ntoa,))
	
	@property
	def addr(self):
		return self._addr

	@property
	def family(self):
		return self._family

	FAM2STR = {socket.AF_INET: 'inet4', socket.AF_INET6: 'inet6'}
	@property
	def familyStr(self):
		return IPAddr.FAM2STR.get(self._family)

	@property
	def instanceType(self):
		return "ip" if self.isValid else "dns"

	@property
	def plen(self):
		return self._plen

	@property
	def raw(self):
		"""The raw address

		Should only be set to a non-empty string if prior address
		conversion wasn't possible
		"""
		return self._raw

	@property
	def isValid(self):
		"""Either the object corresponds to a valid IP address
		"""
		return self._family != socket.AF_UNSPEC

	@property
	def isSingle(self):
		"""Returns whether the object is a single IP address (not DNS and subnet)
		"""
		return self._plen == {socket.AF_INET: 32, socket.AF_INET6: 128}.get(self._family, -1000)

	def __eq__(self, other):
		if self._family == IPAddr.CIDR_RAW and not isinstance(other, IPAddr):
			return self._raw == other
		if not isinstance(other, IPAddr):
			if other is None: return False
			other = IPAddr(other)
		if self._family != other._family: return False
		if self._family == socket.AF_UNSPEC:
			return self._raw == other._raw
		return (
			(self._addr == other._addr) and
			(self._plen == other._plen)
		)

	def __ne__(self, other):
		return not (self == other)

	def __lt__(self, other):
		if self._family == IPAddr.CIDR_RAW and not isinstance(other, IPAddr):
			return self._raw < other
		if not isinstance(other, IPAddr):
			if other is None: return False
			other = IPAddr(other)
		return self._family < other._family or self._addr < other._addr

	def __add__(self, other):
		if not isinstance(other, IPAddr):
			other = IPAddr(other)
		return "%s%s" % (self, other)

	def __radd__(self, other):
		if not isinstance(other, IPAddr):
			other = IPAddr(other)
		return "%s%s" % (other, self)

	def __hash__(self):
		# should be the same as by string (because of possible compare with string):
		return hash(self.ntoa)
		#return hash(self._addr)^hash((self._plen<<16)|self._family)

	@property
	def hexdump(self):
		"""Hex representation of the IP address (for debug purposes)
		"""
		if self._family == socket.AF_INET:
			return "%08x" % self._addr
		elif self._family == socket.AF_INET6:
			return "%032x" % self._addr
		else:
			return ""

	# TODO: could be lazily evaluated
	@property
	def ntoa(self):
		""" represent IP object as text like the deprecated
			C pendant inet.ntoa but address family independent
		"""
		add = ''
		if self.isIPv4:
			# convert network to host byte order
			binary = struct.pack("!L", self._addr)
			if self._plen and self._plen < 32:
				add = "/%d" % self._plen
		elif self.isIPv6:
			# convert network to host byte order
			hi = self._addr >> 64
			lo = self._addr & 0xFFFFFFFFFFFFFFFF
			binary = struct.pack("!QQ", hi, lo)
			if self._plen and self._plen < 128:
				add = "/%d" % self._plen
		else:
			return self._raw
		
		return socket.inet_ntop(self._family, binary) + add

	def getPTR(self, suffix=None):
		""" return the DNS PTR string of the provided IP address object

			If "suffix" is provided it will be appended as the second and top
			level reverse domain.
			If omitted it is implicitly set to the second and top level reverse
			domain of the according IP address family
		"""
		if self.isIPv4:
			exploded_ip = self.ntoa.split(".")
			if suffix is None:
				suffix = "in-addr.arpa."
		elif self.isIPv6:
			exploded_ip = self.hexdump
			if suffix is None:
				suffix = "ip6.arpa."
		else:
			return ""

		return "%s.%s" % (".".join(reversed(exploded_ip)), suffix)

	def getHost(self):
		"""Return the host name (DNS) of the provided IP address object
		"""
		return DNSUtils.ipToName(self.ntoa)

	@property
	def isIPv4(self):
		"""Either the IP object is of address family AF_INET
		"""
		return self.family == socket.AF_INET

	@property
	def isIPv6(self):
		"""Either the IP object is of address family AF_INET6
		"""
		return self.family == socket.AF_INET6

	def isInNet(self, net):
		"""Return either the IP object is in the provided network
		"""
		# if addr-set:
		if isinstance(net, IPAddrSet):
			return self in net
		# if it isn't a valid IP address, try DNS resolution
		if not net.isValid and net.raw != "":
			# Check if IP in DNS
			return self in DNSUtils.dnsToIp(net.raw)

		if self.family != net.family:
			return False
		if self.isIPv4:
			mask = ~(0xFFFFFFFF >> net.plen)
		elif self.isIPv6:
			mask = ~(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF >> net.plen)
		else:
			return False
		
		return (self.addr & mask) == net.addr

	def contains(self, ip):
		"""Return whether the object (as network) contains given IP
		"""
		return isinstance(ip, IPAddr) and (ip == self or ip.isInNet(self))

	def __contains__(self, ip):
		return self.contains(ip)

	# Pre-calculated map: addr to maskplen
	def __getMaskMap():
		m6 = (1 << 128)-1
		m4 = (1 << 32)-1
		mmap = {m6: 128, m4: 32, 0: 0}
		m = 0
		for i in range(0, 128):
			m |= 1 << i
			if i < 32:
				mmap[m ^ m4] = 32-1-i
			mmap[m ^ m6] = 128-1-i
		return mmap

	MAP_ADDR2MASKPLEN = __getMaskMap()

	@property
	def maskplen(self):
		mplen = 0
		if self._maskplen is not None:
			return self._maskplen
		mplen = IPAddr.MAP_ADDR2MASKPLEN.get(self._addr)
		if mplen is None:
			raise ValueError("invalid mask %r, no plen representation" % (str(self),))
		self._maskplen = mplen
		return mplen
		
	@staticmethod
	def masktoplen(mask):
		"""Convert mask string to prefix length

		To be used only for IPv4 masks
		"""
		return IPAddr(mask).maskplen

	@staticmethod
	def searchIP(text):
		"""Search if text is an IP address, and return it if so, else None
		"""
		match = IPAddr.IP_4_6_CRE.match(text)
		if not match:
			return None
		ipstr = match.group('IPv4')
		if ipstr is not None and ipstr != '':
			return ipstr
		return match.group('IPv6')


# An IPv4 compatible IPv6 to be reused
IPAddr.IP6_4COMPAT = IPAddr("::ffff:0:0", 96)


class IPAddrSet(set):

	hasSubNet = 0

	def __init__(self, ips=[]):
		ips, subnet = IPAddrSet._list2set(ips)
		set.__init__(self, ips)
		self.hasSubNet = subnet

	@staticmethod
	def _list2set(ips):
		ips2 = set()
		subnet = 0
		for ip in ips:
			if not isinstance(ip, IPAddr): ip = IPAddr(ip)
			ips2.add(ip)
			subnet += not ip.isSingle
		return ips2, subnet

	@property
	def instanceType(self):
		return "ip-set"

	def set(self, ips):
		ips, subnet = IPAddrSet._list2set(ips)
		self.clear()
		self.update(ips)
		self.hasSubNet = subnet

	def add(self, ip):
		if not isinstance(ip, IPAddr): ip = IPAddr(ip)
		self.hasSubNet |= not ip.isSingle
		set.add(self, ip)

	def __contains__(self, ip):
		if not isinstance(ip, IPAddr): ip = IPAddr(ip)
		# IP can be found directly or IP is in each subnet:
		return set.__contains__(self, ip) or (self.hasSubNet and any(n.contains(ip) for n in self))


class FileIPAddrSet(IPAddrSet):

	# RE matching file://...
	RE_FILE_IGN_IP = re.compile(r'^file:/{0,2}(.*)$')

	fileName = ''
	_shortRepr = None
	maxUpdateLatency = 1 # latency in seconds to update by changes
	_nextCheck = 0
	_fileStats = ()

	def __init__(self, fileName=''):
		self.fileName = fileName
		# self.load() - lazy load on demand by first check (in, __contains__ etc)

	@property
	def instanceType(self):
		return repr(self)

	def __eq__(self, other):
		if id(self) == id(other): return 1
		# to allow remove file-set from list (delIgnoreIP) by its name:
		if isinstance(other, FileIPAddrSet):
			return self.fileName == other.fileName
		m = FileIPAddrSet.RE_FILE_IGN_IP.match(other)
		if m:
			return self.fileName == m.group(1)

	def _isModified(self):
		"""Check whether the file is modified (file stats changed)

		Side effect: if modified, _fileStats will be updated to last known stats of file
		"""
		tm = MyTime.time()
		# avoid to check it always (not often than maxUpdateLatency):
		if tm <= self._nextCheck:
			return None; # no check needed
		self._nextCheck = tm + self.maxUpdateLatency
		stats = os.stat(self.fileName)
		stats = stats.st_mtime, stats.st_ino, stats.st_size
		if self._fileStats != stats:
			self._fileStats = stats
			return True; # modified, needs to be reloaded
		return False; # unmodified

	def load(self, forceReload=False, noError=True):
		"""Load set from file (on demand if needed or by forceReload)
		"""
		try:
			# load only if needed and modified (or first time load on demand)
			if self._isModified() or forceReload:
				with open(self.fileName, 'r') as f:
					ips = f.read()
				ips = splitwords(ips, ignoreComments=True)
				self.set(ips)
		except Exception as e: # pragma: no cover
			self._nextCheck += 60; # increase interval to check (to 1 minute, to avoid log flood on errors)
			if not noError: raise e
			logSys.warning("Retrieving IPs set from %r failed: %s", self.fileName, e)

	def __repr__(self):
		if not self._shortRepr:
			shortfn = os.path.basename(self.fileName)
			if shortfn != self.fileName:
				shortfn = '.../' + shortfn
			self._shortRepr = 'file:' + shortfn + ')'
		return self._shortRepr

	def __contains__(self, ip):
		# load if needed:
		if self.fileName:
			self.load()
		# inherited contains:
		return IPAddrSet.__contains__(self, ip)


def _NetworkInterfacesAddrs(withMask=False):

	# Closure implementing lazy load modules and libc and define _NetworkInterfacesAddrs on demand:
	# Currently tested on Linux only (TODO: implement for MacOS, Solaris, etc)
	try:
		from ctypes import (
			Structure, Union, POINTER,
			pointer, get_errno, cast,
			c_ushort, c_byte, c_void_p, c_char_p, c_uint, c_int, c_uint16, c_uint32
		)
		import ctypes.util
		import ctypes

		class struct_sockaddr(Structure):
			_fields_ = [
				('sa_family', c_ushort),
				('sa_data', c_byte * 14),]

		class struct_sockaddr_in(Structure):
			_fields_ = [
				('sin_family', c_ushort),
				('sin_port', c_uint16),
				('sin_addr', c_byte * 4)]

		class struct_sockaddr_in6(Structure):
			_fields_ = [
				('sin6_family', c_ushort),
				('sin6_port', c_uint16),
				('sin6_flowinfo', c_uint32),
				('sin6_addr', c_byte * 16),
				('sin6_scope_id', c_uint32)]

		class union_ifa_ifu(Union):
			_fields_ = [
				('ifu_broadaddr', POINTER(struct_sockaddr)),
				('ifu_dstaddr', POINTER(struct_sockaddr)),]

		class struct_ifaddrs(Structure):
			pass
		struct_ifaddrs._fields_ = [
			('ifa_next', POINTER(struct_ifaddrs)),
			('ifa_name', c_char_p),
			('ifa_flags', c_uint),
			('ifa_addr', POINTER(struct_sockaddr)),
			('ifa_netmask', POINTER(struct_sockaddr)),
			('ifa_ifu', union_ifa_ifu),
			('ifa_data', c_void_p),]

		libc = ctypes.CDLL(ctypes.util.find_library('c') or "")
		if not libc.getifaddrs: # pragma: no cover
			raise NotImplementedError('libc.getifaddrs is not available')

		def ifap_iter(ifap):
			ifa = ifap.contents
			while True:
				yield ifa
				if not ifa.ifa_next:
					break
				ifa = ifa.ifa_next.contents

		def getfamaddr(ifa, withMask=False):
			sa = ifa.ifa_addr.contents
			fam = sa.sa_family
			if fam == socket.AF_INET:
				sa = cast(pointer(sa), POINTER(struct_sockaddr_in)).contents
				addr = socket.inet_ntop(fam, sa.sin_addr)
				if withMask:
					nm = ifa.ifa_netmask.contents
					if nm is not None and nm.sa_family == socket.AF_INET:
						nm = cast(pointer(nm), POINTER(struct_sockaddr_in)).contents
						addr += '/'+socket.inet_ntop(fam, nm.sin_addr)
				return IPAddr(addr)
			elif fam == socket.AF_INET6:
				sa = cast(pointer(sa), POINTER(struct_sockaddr_in6)).contents
				addr = socket.inet_ntop(fam, sa.sin6_addr)
				if withMask:
					nm = ifa.ifa_netmask.contents
					if nm is not None and nm.sa_family == socket.AF_INET6:
						nm = cast(pointer(nm), POINTER(struct_sockaddr_in6)).contents
						addr += '/'+socket.inet_ntop(fam, nm.sin6_addr)
				return IPAddr(addr)
			return None

		def _NetworkInterfacesAddrs(withMask=False):
			ifap = POINTER(struct_ifaddrs)()
			result = libc.getifaddrs(pointer(ifap))
			if result != 0:
				raise OSError(get_errno())
			del result
			try:
				for ifa in ifap_iter(ifap):
					name = ifa.ifa_name.decode("UTF-8")
					addr = getfamaddr(ifa, withMask)
					if addr:
						yield name, addr
			finally:
				libc.freeifaddrs(ifap)
	
	except Exception as e: # pragma: no cover
		_init_error = NotImplementedError(e)
		def _NetworkInterfacesAddrs():
			raise _init_error

	DNSUtils._NetworkInterfacesAddrs = staticmethod(_NetworkInterfacesAddrs);
	return _NetworkInterfacesAddrs(withMask)

DNSUtils._NetworkInterfacesAddrs = staticmethod(_NetworkInterfacesAddrs);
