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


__author__ = "Yaroslav Halchenko"
__copyright__ = "Copyright (c) 2013 Yaroslav Halchenko"
__license__ = "GPL"

import fileinput
import itertools
import logging
import optparse
import os
import re
import tempfile
import shutil
import sys
import time
import threading
import unittest

from io import StringIO
from functools import wraps

from ..helpers import getLogger, str2LogLevel, getVerbosityFormat, uni_decode
from ..server.ipdns import IPAddr, IPAddrSet, DNSUtils
from ..server.mytime import MyTime
from ..server.utils import Utils
# for action_d.test_smtp :
from ..server import asyncserver
from ..version import version


logSys = getLogger("fail2ban")

TEST_NOW = 1124013600

CONFIG_DIR = os.environ.get('FAIL2BAN_CONFIG_DIR', None)

if not CONFIG_DIR:
# Use heuristic to figure out where configuration files are
	if os.path.exists(os.path.join('config','fail2ban.conf')):
		CONFIG_DIR = 'config'
	else: # pragma: no cover - normally unreachable
		CONFIG_DIR = '/etc/fail2ban'

# Indicates that we've stock config:
STOCK = os.path.exists(os.path.join(CONFIG_DIR, 'fail2ban.conf'))

# During the test cases (or setup) use fail2ban modules from main directory:
os.putenv('PYTHONPATH', os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))

# Default options, if running from installer (setup.py):
class DefaultTestOptions(optparse.Values):
	def __init__(self):
		self.__dict__ = {
			'log_level': None, 'verbosity': None, 'log_lazy': True, 
			'log_traceback': None, 'full_traceback': None,
			'fast': False, 'memory_db': False,
			'no_network': False, 'negate_re': False
		}

#
# Initialization
#
def getOptParser(doc=""):
	Option = optparse.Option
	# use module docstring for help output
	p = optparse.OptionParser(
				usage="%s [OPTIONS] [regexps]\n" % sys.argv[0] + doc,
				version="%prog " + version)

	p.add_options([
		Option('-l', "--log-level",
			   dest="log_level",
			   default=None,
			   help="Log level for the logger to use during running tests"),
		Option('-v', action="count", dest="verbosity",
			   default=None,
			   help="Increase verbosity"),
		Option("--verbosity", action="store", dest="verbosity", type=int,
			   default=None,
			   help="Set numerical level of verbosity (0..4)"),
		Option("--log-direct", action="store_false",
			   dest="log_lazy",
			   default=True,
			   help="Prevent lazy logging inside tests"),
		Option('-n', "--no-network", action="store_true",
			   dest="no_network",
			   help="Do not run tests that require the network"),
		Option('-m', "--memory-db", action="store_true",
			   dest="memory_db",
			   help="Run database tests using memory instead of file"),
		Option('-f', "--fast", action="store_true",
			   dest="fast",
			   help="Try to increase speed of the tests, decreasing of wait intervals, memory database"),
		Option('-i', "--ignore", action="store_true",
			   dest="negate_re",
			   help="negate [regexps] filter to ignore tests matched specified regexps"),
		Option("-t", "--log-traceback", action='store_true',
			   help="Enrich log-messages with compressed tracebacks"),
		Option("--full-traceback", action='store_true',
			   help="Either to make the tracebacks full, not compressed (as by default)"),
		])
	return p

def initProcess(opts):
	# Logger:
	llev = None
	if opts.log_level is not None: # pragma: no cover
		# so we had explicit settings
		llev = str2LogLevel(opts.log_level)
		logSys.setLevel(llev)
	else: # pragma: no cover
		# suppress the logging but it would leave unittests' progress dots
		# ticking, unless like with '-l critical' which would be silent
		# unless error occurs
		logSys.setLevel(logging.CRITICAL)
	opts.log_level = logSys.level

	# Numerical level of verbosity corresponding to a given log "level"
	verbosity = opts.verbosity
	if verbosity is None:
		verbosity = (
			1 if llev is None else \
			4 if llev <= logging.HEAVYDEBUG else \
			3 if llev <= logging.DEBUG else \
			2 if llev <= min(logging.INFO, logging.NOTICE) else \
			1 if llev <= min(logging.WARNING, logging.ERROR) else \
			0 # if llev <= logging.CRITICAL
		)
		opts.verbosity = verbosity

	# Add the default logging handler
	stdout = logging.StreamHandler(sys.stdout)

	fmt = ' %(message)s'

	if opts.log_traceback: # pragma: no cover
		from ..helpers import FormatterWithTraceBack as Formatter
		fmt = (opts.full_traceback and ' %(tb)s' or ' %(tbc)s') + fmt
	else:
		Formatter = logging.Formatter

	# Custom log format for the verbose tests runs
	fmt = getVerbosityFormat(verbosity, fmt)

	#
	stdout.setFormatter(Formatter(fmt))
	logSys.addHandler(stdout)

	# Let know the version
	if opts.verbosity != 0:
		print(("Fail2ban %s test suite. Python %s. Please wait..." \
				% (version, str(sys.version).replace('\n', ''))))

	return opts;


class F2B(DefaultTestOptions):

	MAX_WAITTIME = 60
	MID_WAITTIME = 30

	def __init__(self, opts):
		self.__dict__ = opts.__dict__
		if self.fast: # pragma: no cover - normal mode in travis
			self.memory_db = True
		self.__dict__['share_config'] = {}
	def SkipIfFast(self):
		pass
	def SkipIfNoNetwork(self):
		pass

	def SkipIfCfgMissing(self, **kwargs):
		"""Helper to check action/filter config is available
		"""
		if not STOCK: # pragma: no cover
			if kwargs.get('stock'):
				raise unittest.SkipTest('Skip test because of missing stock-config files')
			for t in ('action', 'filter'):
				v = kwargs.get(t)
				if v is None: continue
				if os.path.splitext(v)[1] == '': v += '.conf'
				if not os.path.exists(os.path.join(CONFIG_DIR, t+'.d', v)):
					raise unittest.SkipTest('Skip test because of missing %s-config for %r' % (t, v))

	def skip_if_cfg_missing(self, **decargs):
		"""Helper decorator to check action/filter config is available
		"""
		def _deco_wrapper(f):
			@wraps(f)
			def wrapper(self, *args, **kwargs):
				unittest.F2B.SkipIfCfgMissing(**decargs)
				return f(self, *args, **kwargs)
			return wrapper
		return _deco_wrapper

	def maxWaitTime(self, wtime=True):
		if isinstance(wtime, bool) and wtime:
			wtime = self.MAX_WAITTIME
		# short only integer interval (avoid by conditional wait with callable, and dual 
		# wrapping in some routines, if it will be called twice):
		if self.fast and isinstance(wtime, int):
			wtime = float(wtime) / 2.5
		return wtime


def with_tmpdir(f):
	"""Helper decorator to create a temporary directory

	Directory gets removed after function returns, regardless
	if exception was thrown of not
	"""
	@wraps(f)
	def wrapper(self, *args, **kwargs):
		tmp = tempfile.mkdtemp(prefix="f2b-temp")
		try:
			return f(self, tmp, *args, **kwargs)
		finally:
			# clean up
			shutil.rmtree(tmp)
	return wrapper

def with_alt_time(f):
	"""Helper decorator to execute test in alternate (fixed) test time."""
	@wraps(f)
	def wrapper(self, *args, **kwargs):
		setUpMyTime()
		try:
			return f(self, *args, **kwargs)
		finally:
			tearDownMyTime()
	return wrapper


def initTests(opts):
	## if running from installer (setup.py):
	if not opts:
		opts = initProcess(DefaultTestOptions())
	unittest.F2B = F2B(opts)
	# --fast :
	if unittest.F2B.fast: # pragma: no cover
		# racy decrease default sleep intervals to test it faster 
		# (prevent long sleeping during test cases ... less time goes to sleep):
		Utils.DEFAULT_SLEEP_TIME = 0.0025
		Utils.DEFAULT_SLEEP_INTERVAL = 0.0005
		Utils.DEFAULT_SHORT_INTERVAL = 0.0001
		def F2B_SkipIfFast():
			raise unittest.SkipTest('Skip test because of "--fast"')
		unittest.F2B.SkipIfFast = F2B_SkipIfFast
	else:
		# smaller inertance inside test-cases (little speedup):
		Utils.DEFAULT_SLEEP_TIME = 0.025
		Utils.DEFAULT_SLEEP_INTERVAL = 0.005
		Utils.DEFAULT_SHORT_INTERVAL = 0.0005
		# sleep intervals are large - use replacement for sleep to check time to sleep:
		_org_sleep = time.sleep
		def _new_sleep(v):
			if v > 0.25: # pragma: no cover
				raise ValueError('[BAD-CODE] To long sleep interval: %s, try to use conditional Utils.wait_for instead' % v)
			_org_sleep(v)
		time.sleep = _new_sleep
	# --no-network :
	if unittest.F2B.no_network: # pragma: no cover
		def F2B_SkipIfNoNetwork():
			raise unittest.SkipTest('Skip test because of "--no-network"')
		unittest.F2B.SkipIfNoNetwork = F2B_SkipIfNoNetwork

	# persistently set time zone to CET (used in zone-related test-cases),
	# yoh: we need to adjust TZ to match the one used by Cyril so all the timestamps match
	# This offset corresponds to Europe/Zurich timezone.  Specifying it
	# explicitly allows to avoid requiring tzdata package to be installed during
	# testing.   See https://bugs.debian.org/855920 for more information
	os.environ['TZ'] = 'CET-01CEST-02,M3.5.0,M10.5.0'
	time.tzset()
	# set alternate now for time related test cases:
	MyTime.setAlternateNow(TEST_NOW)

	# precache all invalid ip's (TEST-NET-1, ..., TEST-NET-3 according to RFC 5737):
	c = DNSUtils.CACHE_ipToName
	c.clear = lambda: logSys.warning('clear CACHE_ipToName is disabled in test suite')
	# increase max count and max time (too many entries, long time testing):
	c.setOptions(maxCount=10000, maxTime=5*60)
	for i in range(256):
		c.set('192.0.2.%s' % i, None)
		c.set('198.51.100.%s' % i, None)
		c.set('203.0.113.%s' % i, None)
		c.set('2001:db8::%s' %i, 'test-host')
	# some legal ips used in our test cases (prevent slow dns-resolving and failures if will be changed later):
	c.set('2001:db8::ffff', 'test-other')
	c.set('87.142.124.10', 'test-host')
	if unittest.F2B.no_network: # pragma: no cover
		if unittest.F2B.fast: # pragma: no cover
			for i in ('127.0.0.1', '::1'): # DNSUtils.dnsToIp('localhost')
				c.set(i, 'localhost')
		# precache all ip to dns used in test cases:
		c.set('192.0.2.888', None)
		c.set('8.8.4.4', 'dns.google')
		c.set('8.8.8.8', 'dns.google')
		c.set('199.9.14.201', 'b-2017.b.root-servers.org')
		# precache all dns to ip's used in test cases:
		c = DNSUtils.CACHE_nameToIp
		c.clear = lambda: logSys.warning('clear CACHE_nameToIp is disabled in test suite')
		for i in (
			('999.999.999.999', set()),
			('abcdef.abcdef', set()),
			('192.168.0.', set()),
			('failed.dns.ch', set()),
			('doh1.2.3.4.buga.xxxxx.yyy.invalid', set()),
			('1.2.3.4.buga.xxxxx.yyy.invalid', set()),
			('fail2ban.org', set([IPAddr('2001:bc8:1200:6:208:a2ff:fe0c:61f8'), IPAddr('51.159.55.100')])),
			('www.fail2ban.org', set([IPAddr('2001:bc8:1200:6:208:a2ff:fe0c:61f8'), IPAddr('51.159.55.100')])),
		):
			c.set(*i)
		# if fast - precache all host names as localhost addresses (speed-up getSelfIPs/ignoreself):
		if unittest.F2B.fast: # pragma: no cover
			ips = set([IPAddr('127.0.0.1'), IPAddr('::1')]); # DNSUtils.dnsToIp('localhost')
			for i in DNSUtils.getSelfNames():
				c.set(i, ips)
	# some test subnets (although normally they are not resolved to addr/cidr,
	# we'll use IPAddrSet here to seek through the resolved subnet in tests):
	c = DNSUtils.CACHE_nameToIp
	c.set('test-local-net', IPAddrSet([IPAddr('127.0.0.1/8'), IPAddr('::1')]))
	c.set('test-subnet-a', IPAddrSet([IPAddr('192.0.2.0/29'), IPAddr('2001:db8::0/125')]));   # 192.0.2.0  .. 192.0.2.7,  2001:db8::00 .. 2001:db8::07
	c.set('test-subnet-b', IPAddrSet([IPAddr('192.0.2.16/29'), IPAddr('2001:db8::10/125')])); # 192.0.2.16 .. 192.0.2.23, 2001:db8::10 .. 2001:db8::17


def mtimesleep():
	# no sleep now should be necessary since polling tracks now not only
	# mtime but also ino and size
	pass

old_TZ = os.environ.get('TZ', None)


def setUpMyTime():
	# Set the time to a fixed, known value
	# Sun Aug 14 12:00:00 CEST 2005
	MyTime.setTime(TEST_NOW)


def tearDownMyTime():
	MyTime.myTime = None


def gatherTests(regexps=None, opts=None):
	initTests(opts)
	# Import all the test cases here instead of a module level to
	# avoid circular imports
	from . import banmanagertestcase
	from . import clientbeautifiertestcase
	from . import clientreadertestcase
	from . import tickettestcase
	from . import failmanagertestcase
	from . import filtertestcase
	from . import servertestcase
	from . import datedetectortestcase
	from . import actiontestcase
	from . import actionstestcase
	from . import sockettestcase
	from . import misctestcase
	from . import databasetestcase
	from . import observertestcase
	from . import samplestestcase
	from . import fail2banclienttestcase
	from . import fail2banregextestcase

	if not regexps: # pragma: no cover
		tests = unittest.TestSuite()
	else: # pragma: no cover
		class FilteredTestSuite(unittest.TestSuite):
			_regexps = [re.compile(r) for r in regexps]

			def addTest(self, suite):
				matched = []
				for test in suite:
					# test of suite loaded with loadTestsFromName may be a suite self:
					if isinstance(test, unittest.TestSuite): # pragma: no cover
						self.addTest(test)
						continue
					# filter by regexp:
					s = str(test)
					for r in self._regexps:
						m = r.search(s)
						if (m if not opts.negate_re else not m):
							matched.append(test)
							break
				for test in matched:
					super(FilteredTestSuite, self).addTest(test)

		tests = FilteredTestSuite()

	loadTests = unittest.defaultTestLoader.loadTestsFromTestCase;

	# Server
	tests.addTest(loadTests(servertestcase.Transmitter))
	tests.addTest(loadTests(servertestcase.JailTests))
	tests.addTest(loadTests(servertestcase.RegexTests))
	tests.addTest(loadTests(servertestcase.LoggingTests))
	tests.addTest(loadTests(servertestcase.ServerConfigReaderTests))
	tests.addTest(loadTests(actiontestcase.CommandActionTest))
	tests.addTest(loadTests(actionstestcase.ExecuteActions))
	# Ticket, BanTicket, FailTicket
	tests.addTest(loadTests(tickettestcase.TicketTests))
	# FailManager
	tests.addTest(loadTests(failmanagertestcase.AddFailure))
	tests.addTest(loadTests(failmanagertestcase.FailmanagerComplex))
	# BanManager
	tests.addTest(loadTests(banmanagertestcase.AddFailure))
	try:
		import dns
		tests.addTest(loadTests(banmanagertestcase.StatusExtendedCymruInfo))
	except ImportError: # pragma: no cover
		pass
	
	# ClientBeautifier
	tests.addTest(loadTests(clientbeautifiertestcase.BeautifierTest))

	# ClientReaders
	tests.addTest(loadTests(clientreadertestcase.ConfigReaderTest))
	tests.addTest(loadTests(clientreadertestcase.JailReaderTest))
	tests.addTest(loadTests(clientreadertestcase.FilterReaderTest))
	tests.addTest(loadTests(clientreadertestcase.JailsReaderTest))
	tests.addTest(loadTests(clientreadertestcase.JailsReaderTestCache))
	# CSocket and AsyncServer
	tests.addTest(loadTests(sockettestcase.Socket))
	tests.addTest(loadTests(sockettestcase.ClientMisc))
	# Misc helpers
	tests.addTest(loadTests(misctestcase.HelpersTest))
	tests.addTest(loadTests(misctestcase.SetupTest))
	tests.addTest(loadTests(misctestcase.TestsUtilsTest))
	tests.addTest(loadTests(misctestcase.MyTimeTest))
	# Database
	tests.addTest(loadTests(databasetestcase.DatabaseTest))
	# Observer
	tests.addTest(loadTests(observertestcase.ObserverTest))
	tests.addTest(loadTests(observertestcase.BanTimeIncr))
	tests.addTest(loadTests(observertestcase.BanTimeIncrDB))

	# Filter
	tests.addTest(loadTests(filtertestcase.IgnoreIP))
	tests.addTest(loadTests(filtertestcase.BasicFilter))
	tests.addTest(loadTests(filtertestcase.LogFile))
	tests.addTest(loadTests(filtertestcase.LogFileMonitor))
	tests.addTest(loadTests(filtertestcase.LogFileFilterPoll))
	# each test case class self will check no network, and skip it (we see it in log)
	tests.addTest(loadTests(filtertestcase.IgnoreIPDNS))
	tests.addTest(loadTests(filtertestcase.GetFailures))
	tests.addTest(loadTests(filtertestcase.DNSUtilsTests))
	tests.addTest(loadTests(filtertestcase.DNSUtilsNetworkTests))
	tests.addTest(loadTests(filtertestcase.JailTests))

	# DateDetector
	tests.addTest(loadTests(datedetectortestcase.DateDetectorTest))
	tests.addTest(loadTests(datedetectortestcase.CustomDateFormatsTest))
	# Filter Regex tests with sample logs
	tests.addTest(loadTests(samplestestcase.FilterSamplesRegex))

	# bin/fail2ban-client, bin/fail2ban-server
	tests.addTest(loadTests(fail2banclienttestcase.Fail2banClientTest))
	tests.addTest(loadTests(fail2banclienttestcase.Fail2banServerTest))
	# bin/fail2ban-regex
	tests.addTest(loadTests(fail2banregextestcase.Fail2banRegexTest))

	#
	# Python action testcases
	#
	testloader = unittest.TestLoader()
	from . import action_d
	for file_ in os.listdir(
		os.path.abspath(os.path.dirname(action_d.__file__))):
		if file_.startswith("test_") and file_.endswith(".py"):
			tests.addTest(testloader.loadTestsFromName(
				"%s.%s" % (action_d.__name__, os.path.splitext(file_)[0])))

	#
	# Extensive use-tests of different available filters backends
	#

	from ..server.filterpoll import FilterPoll
	filters = [FilterPoll]					  # always available

	# Additional filters available only if external modules are available
	# yoh: Since I do not know better way for parametric tests
	#      with good old unittest
	try:
		from ..server.filterpyinotify import FilterPyinotify
		filters.append(FilterPyinotify)
	except ImportError as e: # pragma: no cover
		logSys.warning("I: Skipping pyinotify backend testing. Got exception '%s'" % e)

	for Filter_ in filters:
		tests.addTest(loadTests(
			filtertestcase.get_monitor_failures_testcase(Filter_)))
	try: # pragma: systemd no cover
		from ..server.filtersystemd import FilterSystemd
		tests.addTest(loadTests(filtertestcase.get_monitor_failures_journal_testcase(FilterSystemd)))
	except ImportError as e: # pragma: no cover
		logSys.warning("I: Skipping systemd backend testing. Got exception '%s'" % e)

	# Server test for logging elements which break logging used to support
	# testcases analysis
	tests.addTest(loadTests(servertestcase.TransmitterLogging))

	return tests


#
# Forwards compatibility of unittest.TestCase for some early python versions
#

import difflib, pprint
if not hasattr(unittest.TestCase, 'assertDictEqual'):
	def assertDictEqual(self, d1, d2, msg=None):
		self.assertTrue(isinstance(d1, dict), 'First argument is not a dictionary')
		self.assertTrue(isinstance(d2, dict), 'Second argument is not a dictionary')
		if d1 != d2:
			standardMsg = '%r != %r' % (d1, d2)
			diff = ('\n' + '\n'.join(difflib.ndiff(
				pprint.pformat(d1).splitlines(),
				pprint.pformat(d2).splitlines())))
			msg = msg or (standardMsg + diff)
			self.fail(msg)
	unittest.TestCase.assertDictEqual = assertDictEqual

def assertSortedEqual(self, a, b, level=1, nestedOnly=False, key=repr, msg=None):
	"""Compare complex elements (like dict, list or tuple) in sorted order until
	level 0 not reached (initial level = -1 meant all levels),
	or if nestedOnly set to True and some of the objects still contains nested lists or dicts.
	"""
	# used to recognize having element as nested dict, list or tuple:
	def _is_nested(v):
		if isinstance(v, dict):
			return any(isinstance(v, (dict, list, tuple)) for v in v.values())
		return any(isinstance(v, (dict, list, tuple)) for v in v)
	if nestedOnly:
		_nest_sorted = sorted
	else:
		def _nest_sorted(v, key=key):
			if isinstance(v, (set, list, tuple)):
				return sorted(list(_nest_sorted(v, key) for v in v), key=key)
			return v
	# level comparison routine:
	def _assertSortedEqual(a, b, level, nestedOnly, key):
		# first the lengths:
		if len(a) != len(b):
			raise ValueError('%r != %r' % (a, b))
		# if not allow sorting of nested - just compare directly:
		if not level and (nestedOnly and (not _is_nested(a) and not _is_nested(b))):
			if a == b:
				return
			raise ValueError('%r != %r' % (a, b))
		if isinstance(a, dict) and isinstance(b, dict): # compare dict's:
			for k, v1 in a.items():
				v2 = b[k]
				if isinstance(v1, (dict, list, tuple)) and isinstance(v2, (dict, list, tuple)):
					_assertSortedEqual(v1, v2, level-1 if level != 0 else 0, nestedOnly, key)
				elif v1 != v2:
					raise ValueError('%r != %r' % (a, b))
		else: # list, tuple, something iterable:
			a = _nest_sorted(a, key=key)
			b = _nest_sorted(b, key=key)
			for v1, v2 in zip(a, b):
				if isinstance(v1, (dict, list, tuple)) and isinstance(v2, (dict, list, tuple)):
					_assertSortedEqual(v1, v2, level-1 if level != 0 else 0, nestedOnly, key)
				elif v1 != v2:
					raise ValueError('%r != %r' % (a, b))
	# compare and produce assertion-error by exception:
	try:
		_assertSortedEqual(a, b, level, nestedOnly, key)
	except Exception as e:
		standardMsg = e.args[0] if isinstance(e, ValueError) else (str(e) + "\nwithin:")
		diff = ('\n' + '\n'.join(difflib.ndiff(
			pprint.pformat(a).splitlines(),
			pprint.pformat(b).splitlines())))
		msg = msg or (standardMsg + diff)
		self.fail(msg)
unittest.TestCase.assertSortedEqual = assertSortedEqual

# always custom following methods, because we use atm better version of both (support generators)
if True: ## if not hasattr(unittest.TestCase, 'assertIn'):
	def assertIn(self, a, b, msg=None):
		bb = b
		wrap = False
		if msg is None and hasattr(b, '__iter__') and not isinstance(b, str):
			b, bb = itertools.tee(b)
			wrap = True
		if a not in b:
			if wrap: bb = list(bb)
			msg = msg or "%r was not found in %r" % (a, bb)
			self.fail(msg)
	unittest.TestCase.assertIn = assertIn
	def assertNotIn(self, a, b, msg=None):
		bb = b
		wrap = False
		if msg is None and hasattr(b, '__iter__') and not isinstance(b, str):
			b, bb = itertools.tee(b)
			wrap = True
		if a in b:
			if wrap: bb = list(bb)
			msg = msg or "%r unexpectedly found in %r" % (a, bb)
			self.fail(msg)
	unittest.TestCase.assertNotIn = assertNotIn

_org_setUp = unittest.TestCase.setUp
def _customSetUp(self):
	# print('=='*10, self)
	# so if DEBUG etc -- show them (and log it in travis)!
	if unittest.F2B.log_level <= logging.DEBUG: # pragma: no cover
		sys.stderr.write("\n")
		logSys.debug('='*10 + ' %s ' + '='*20, self.id())
	_org_setUp(self)
	if unittest.F2B.verbosity > 2: # pragma: no cover
		self.__startTime = time.time()

_org_tearDown = unittest.TestCase.tearDown
def _customTearDown(self):
	if unittest.F2B.verbosity > 2: # pragma: no cover
		sys.stderr.write(" %.3fs -- " % (time.time() - self.__startTime,))

unittest.TestCase.setUp = _customSetUp
unittest.TestCase.tearDown = _customTearDown


class LogCaptureTestCase(unittest.TestCase):

	class _MemHandler(logging.Handler):
		"""Logging handler helper
		
		Affords not to delegate logging to StreamHandler at all,
		format lazily on demand in getvalue.
		Increases performance inside the LogCaptureTestCase tests, because there
		the log level set to DEBUG.
		"""

		def __init__(self, lazy=True):
			self._lock = threading.Lock()
			self._val = ''
			self._dirty = 0
			self._recs = list()
			self._nolckCntr = 0
			self._strm = StringIO()
			logging.Handler.__init__(self)
			if lazy:
				self.handle = self._handle_lazy
			
		def truncate(self, size=None):
			"""Truncate the internal buffer and records."""
			if size: # pragma: no cover - not implemented now
				raise Exception('invalid size argument: %r, should be None or 0' % size)
			self._val = ''
			with self._lock:
				self._dirty = 0
				self._recs = list()
				self._strm.truncate(0)

		def __write(self, record):
			try:
				msg = record.getMessage() + '\n'
				try:
					self._strm.write(msg)
				except UnicodeEncodeError: # pragma: no cover - normally unreachable now
					self._strm.write(msg.encode('UTF-8', 'replace'))
			except Exception as e: # pragma: no cover - normally unreachable
				self._strm.write('Error by logging handler: %r' % e)

		def getvalue(self):
			"""Return current buffer as whole string."""
			# if cached (still unchanged/no write operation), we don't need to enter lock:
			if not self._dirty:
				return self._val
			# try to lock, if not possible - return cached/empty (max 5 times):
			lck = self._lock.acquire(False)
			# if records changed:
			if self._dirty & 2:
				if not lck: # pragma: no cover (may be too sporadic on slow systems)
					self._nolckCntr += 1
					if self._nolckCntr <= 5:
						return self._val
					self._nolckCntr = 0
					self._lock.acquire()
				# minimize time of lock, avoid dead-locking during cross lock within self._strm ...
				try:
					self._dirty &= ~3 # reset dirty records/buffer flag before cache value built
					recs = self._recs
					self._recs = list()
				finally:
					self._lock.release()
				# submit already emitted (delivered to handle) records:
				for record in recs:
					self.__write(record)
			elif lck: # pragma: no cover - too sporadic for coverage
				# reset dirty buffer flag (if we can lock, otherwise just next time):
				self._dirty &= ~1 # reset dirty buffer flag
				self._lock.release()
			# cache (outside of log to avoid dead-locking during cross lock within self._strm):
			self._val = self._strm.getvalue()
			# return current string value:
			return self._val
			 
		def handle(self, record): # pragma: no cover
			"""Handle the specified record direct (not lazy)"""
			self.__write(record)
			# string buffer changed:
			with self._lock:
				self._dirty |= 1 # buffer changed

		def _handle_lazy(self, record):
			"""Lazy handle the specified record on demand"""
			with self._lock:
				self._recs.append(record)
				# logged - causes changed string buffer (signal by set _dirty):
				self._dirty |= 2 # records changed

	def setUp(self):
		# For extended testing of what gets output into logging
		# system, we will redirect it to a string
		# Keep old settings
		self._old_level = logSys.level
		self._old_handlers = logSys.handlers
		# Let's log everything into a string
		self._log = LogCaptureTestCase._MemHandler(unittest.F2B.log_lazy)
		logSys.handlers = [self._log]
		# lowest log level to capture messages (expected in tests) is Lev.9
		if self._old_level <= logging.DEBUG: # pragma: no cover
			logSys.handlers += self._old_handlers
		if self._old_level > logging.DEBUG-1:
			logSys.setLevel(logging.DEBUG-1)
		super(LogCaptureTestCase, self).setUp()

	def tearDown(self):
		"""Call after every test case."""
		# print "O: >>%s<<" % self._log.getvalue()
		self.pruneLog()
		self._log.close()
		logSys.handlers = self._old_handlers
		logSys.setLevel(self._old_level)
		super(LogCaptureTestCase, self).tearDown()

	def _is_logged(self, *s, **kwargs):
		logged = self._log.getvalue()
		if not kwargs.get('all', False):
			# at least one entry should be found:
			for s_ in s:
				if s_ in logged:
					return True
			if True: # pragma: no cover
				return False
		else:
			# each entry should be found:
			for s_ in s:
				if s_ not in logged: # pragma: no cover
					return False
			return True

	def assertLogged(self, *s, **kwargs):
		"""Assert that one of the strings was logged

		Preferable to assertTrue(self._is_logged(..)))
		since provides message with the actual log.

		Parameters
		----------
		s : string or list/set/tuple of strings
		  Test should succeed if string (or any of the listed) is present in the log
		all : boolean (default False) if True should fail if any of s not logged
		"""
		wait = kwargs.get('wait', None)
		if wait:
			wait = unittest.F2B.maxWaitTime(wait)
			res = Utils.wait_for(lambda: self._is_logged(*s, **kwargs), wait)
		else:
			res = self._is_logged(*s, **kwargs)
		if not kwargs.get('all', False):
			# at least one entry should be found:
			if not res:
				logged = self._log.getvalue()
				self.fail("None among %r was found in the log%s: ===\n%s===" % (s, 
					((', waited %s' % wait) if wait else ''), logged))
		else:
			# each entry should be found:
			if not res:
				logged = self._log.getvalue()
				for s_ in s:
					if s_ not in logged:
						self.fail("%r was not found in the log%s: ===\n%s===" % (s_, 
							((', waited %s' % wait) if wait else ''), logged))

	def assertNotLogged(self, *s, **kwargs):
		"""Assert that strings were not logged

		Parameters
		----------
		s : string or list/set/tuple of strings
		  Test should succeed if the string (or at least one of the listed) is not
		  present in the log
		all : boolean (default False) if True should fail if any of s logged
		"""
		logged = self._log.getvalue()
		if len(s) > 1 and not kwargs.get('all', False):
			for s_ in s:
				if s_ not in logged:
					return
			self.fail("All of the %r were found present in the log: ===\n%s===" % (s, logged))
		else:
			for s_ in s:
				if s_ in logged:
					self.fail("%r was found in the log: ===\n%s===" % (s_, logged))

	def pruneLog(self, logphase=None):
		self._log.truncate(0)
		if logphase:
			logSys.debug('='*5 + ' %s ' + '='*5, logphase)

	def getLog(self):
		return self._log.getvalue()

	@staticmethod
	def dumpFile(fn, handle=logSys.debug):
		"""Helper which outputs content of the file at HEAVYDEBUG loglevels"""
		if (handle != logSys.debug or logSys.getEffectiveLevel() <= logging.DEBUG):
			handle('---- ' + fn + ' ----')
			for line in fileinput.input(fn):
				line = line.rstrip('\n')
				handle(line)
			handle('-'*30)


pid_exists = Utils.pid_exists
