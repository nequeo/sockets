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

# Author: Cyril Jaquier
# 

__author__ = "Cyril Jaquier"
__copyright__ = "Copyright (c) 2004 Cyril Jaquier"
__license__ = "GPL"

import textwrap

def output(s):
	"""Default output handler for printing protocol. 
  Used to ease mocking in the test cases.
	"""
	print(s)

##
# Describes the protocol used to communicate with the server.

class dotdict(dict):
	def __getattr__(self, name):
		return self[name]

CSPROTO = dotdict({
	"EMPTY":  b"",
	"END":    b"<F2B_END_COMMAND>",
	"CLOSE":  b"<F2B_CLOSE_COMMAND>"
})

protocol = [
['', "BASIC", ""],
["start", "starts the server and the jails"], 
["restart", "restarts the server"], 
["restart [--unban] [--if-exists] <JAIL>", "restarts the jail <JAIL> (alias for 'reload --restart ... <JAIL>')"], 
["reload [--restart] [--unban] [--all]", "reloads the configuration without restarting of the server, the option '--restart' activates completely restarting of affected jails, thereby can unban IP addresses (if option '--unban' specified)"],
["reload [--restart] [--unban] [--if-exists] <JAIL>", "reloads the jail <JAIL>, or restarts it (if option '--restart' specified)"],
["stop", "stops all jails and terminate the server"], 
["unban --all", "unbans all IP addresses (in all jails and database)"],
["unban <IP> ... <IP>", "unbans <IP> (in all jails and database)"],
["banned", "return jails with banned IPs as dictionary"],
["banned <IP> ... <IP>]", "return list(s) of jails where given IP(s) are banned"],
["status", "gets the current status of the server"], 
["status --all [FLAVOR]", "gets the current status of all jails, with optional output style [FLAVOR]. Flavors: 'basic' (default), 'cymru', 'short', 'stats'"],
["stat[istic]s", "gets the current statistics of all jails as table"],
["ping", "tests if the server is alive"],
["echo", "for internal usage, returns back and outputs a given string"],
["version", "return the server version"],
['', "LOGGING", ""],
["set loglevel <LEVEL>", "sets logging level to <LEVEL>. Levels: CRITICAL, ERROR, WARNING, NOTICE, INFO, "
	"DEBUG, TRACEDEBUG, HEAVYDEBUG or corresponding numeric value (50-5)"], 
["get loglevel", "gets the logging level"], 
["set logtarget <TARGET>", "sets logging target to <TARGET>. Can be STDOUT, STDERR, SYSLOG, SYSTEMD-JOURNAL or a file"], 
["get logtarget", "gets logging target"], 
["set syslogsocket auto|<SOCKET>", "sets the syslog socket path to auto or <SOCKET>. Only used if logtarget is SYSLOG"],
["get syslogsocket", "gets syslog socket path"],
["flushlogs", "flushes the logtarget if a file and reopens it. For log rotation."], 
['', "DATABASE", ""],
["set dbfile <FILE>", "set the location of fail2ban persistent datastore. Set to \"None\" to disable"], 
["get dbfile", "get the location of fail2ban persistent datastore"], 
["set dbmaxmatches <INT>", "sets the max number of matches stored in database per ticket"], 
["get dbmaxmatches", "gets the max number of matches stored in database per ticket"], 
["set dbpurgeage <SECONDS>", "sets the max age in <SECONDS> that history of bans will be kept"], 
["get dbpurgeage", "gets the max age in seconds that history of bans will be kept"], 
['', "JAIL CONTROL", ""],
["add <JAIL> <BACKEND>", "creates <JAIL> using <BACKEND>"], 
["start <JAIL>", "starts the jail <JAIL>"], 
["stop <JAIL>", "stops the jail <JAIL>. The jail is removed"], 
["status <JAIL> [FLAVOR]", "gets the current status of <JAIL>, with optional output style [FLAVOR]. Flavors: 'basic' (default), 'cymru', 'short', 'stats'"],
['', "JAIL CONFIGURATION", ""],
["set <JAIL> idle on|off", "sets the idle state of <JAIL>"], 
["set <JAIL> ignoreself true|false", "allows the ignoring of own IP addresses"], 
["set <JAIL> addignoreip <IP>", "adds <IP> to the ignore list of <JAIL>"], 
["set <JAIL> delignoreip <IP>", "removes <IP> from the ignore list of <JAIL>"], 
["set <JAIL> ignorecommand <VALUE>", "sets ignorecommand of <JAIL>"],
["set <JAIL> ignorecache <VALUE>", "sets ignorecache of <JAIL>"],
["set <JAIL> addlogpath <FILE> ['tail']", "adds <FILE> to the monitoring list of <JAIL>, optionally starting at the 'tail' of the file (default 'head')."], 
["set <JAIL> dellogpath <FILE>", "removes <FILE> from the monitoring list of <JAIL>"],
["set <JAIL> logencoding <ENCODING>", "sets the <ENCODING> of the log files for <JAIL>"],
["set <JAIL> addjournalmatch <MATCH>", "adds <MATCH> to the journal filter of <JAIL>"],
["set <JAIL> deljournalmatch <MATCH>", "removes <MATCH> from the journal filter of <JAIL>"],
["set <JAIL> addfailregex <REGEX>", "adds the regular expression <REGEX> which must match failures for <JAIL>"], 
["set <JAIL> delfailregex <INDEX>", "removes the regular expression at <INDEX> for failregex"], 
["set <JAIL> addignoreregex <REGEX>", "adds the regular expression <REGEX> which should match pattern to exclude for <JAIL>"],
["set <JAIL> delignoreregex <INDEX>", "removes the regular expression at <INDEX> for ignoreregex"], 
["set <JAIL> findtime <TIME>", "sets the number of seconds <TIME> for which the filter will look back for <JAIL>"], 
["set <JAIL> bantime <TIME>", "sets the number of seconds <TIME> a host will be banned for <JAIL>"], 
["set <JAIL> datepattern <PATTERN>", "sets the <PATTERN> used to match date/times for <JAIL>"],
["set <JAIL> usedns <VALUE>", "sets the usedns mode for <JAIL>"],
["set <JAIL> attempt <IP> [<failure1> ... <failureN>]", "manually notify about <IP> failure"], 
["set <JAIL> banip <IP> ... <IP>", "manually Ban <IP> for <JAIL>"], 
["set <JAIL> unbanip [--report-absent] <IP> ... <IP>", "manually Unban <IP> in <JAIL>"], 
["set <JAIL> maxretry <RETRY>", "sets the number of failures <RETRY> before banning the host for <JAIL>"], 
["set <JAIL> maxmatches <INT>", "sets the max number of matches stored in memory per ticket in <JAIL>"], 
["set <JAIL> maxlines <LINES>", "sets the number of <LINES> to buffer for regex search for <JAIL>"], 
["set <JAIL> addaction <ACT>[ <PYTHONFILE> <JSONKWARGS>]", "adds a new action named <ACT> for <JAIL>. Optionally for a Python based action, a <PYTHONFILE> and <JSONKWARGS> can be specified, else will be a Command Action"], 
["set <JAIL> delaction <ACT>", "removes the action <ACT> from <JAIL>"], 
["", "COMMAND ACTION CONFIGURATION", ""],
["set <JAIL> action <ACT> actionstart <CMD>", "sets the start command <CMD> of the action <ACT> for <JAIL>"], 
["set <JAIL> action <ACT> actionstop <CMD>", "sets the stop command <CMD> of the action <ACT> for <JAIL>"], 
["set <JAIL> action <ACT> actioncheck <CMD>", "sets the check command <CMD> of the action <ACT> for <JAIL>"], 
["set <JAIL> action <ACT> actionban <CMD>", "sets the ban command <CMD> of the action <ACT> for <JAIL>"],
["set <JAIL> action <ACT> actionunban <CMD>", "sets the unban command <CMD> of the action <ACT> for <JAIL>"], 
["set <JAIL> action <ACT> timeout <TIMEOUT>", "sets <TIMEOUT> as the command timeout in seconds for the action <ACT> for <JAIL>"],
["", "GENERAL ACTION CONFIGURATION", ""],
["set <JAIL> action <ACT> <PROPERTY> <VALUE>", "sets the <VALUE> of <PROPERTY> for the action <ACT> for <JAIL>"],
["set <JAIL> action <ACT> <METHOD>[ <JSONKWARGS>]", "calls the <METHOD> with <JSONKWARGS> for the action <ACT> for <JAIL>"],
['', "JAIL INFORMATION", ""],
["get <JAIL> banned", "return banned IPs of <JAIL>"],
["get <JAIL> banned <IP> ... <IP>]", "return 1 if IP is banned in <JAIL> otherwise 0, or a list of 1/0 for multiple IPs"],
["get <JAIL> logpath", "gets the list of the monitored files for <JAIL>"],
["get <JAIL> logencoding", "gets the encoding of the log files for <JAIL>"],
["get <JAIL> journalmatch", "gets the journal filter match for <JAIL>"],
["get <JAIL> ignoreself", "gets the current value of the ignoring the own IP addresses"],
["get <JAIL> ignoreip", "gets the list of ignored IP addresses for <JAIL>"],
["get <JAIL> ignorecommand", "gets ignorecommand of <JAIL>"],
["get <JAIL> failregex", "gets the list of regular expressions which matches the failures for <JAIL>"],
["get <JAIL> ignoreregex", "gets the list of regular expressions which matches patterns to ignore for <JAIL>"],
["get <JAIL> findtime", "gets the time for which the filter will look back for failures for <JAIL>"],
["get <JAIL> bantime", "gets the time a host is banned for <JAIL>"],
["get <JAIL> datepattern", "gets the pattern used to match date/times for <JAIL>"],
["get <JAIL> usedns", "gets the usedns setting for <JAIL>"],
["get <JAIL> banip [<SEP>|--with-time]", "gets the list of of banned IP addresses for <JAIL>. Optionally the separator character ('<SEP>', default is space) or the option '--with-time' (printing the times of ban) may be specified. The IPs are ordered by end of ban."],
["get <JAIL> maxretry", "gets the number of failures allowed for <JAIL>"],
["get <JAIL> maxmatches", "gets the max number of matches stored in memory per ticket in <JAIL>"], 
["get <JAIL> maxlines", "gets the number of lines to buffer for <JAIL>"],
["get <JAIL> actions", "gets a list of actions for <JAIL>"],
["", "COMMAND ACTION INFORMATION",""],
["get <JAIL> action <ACT> actionstart", "gets the start command for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> actionstop", "gets the stop command for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> actioncheck", "gets the check command for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> actionban", "gets the ban command for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> actionunban", "gets the unban command for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> timeout", "gets the command timeout in seconds for the action <ACT> for <JAIL>"],
["", "GENERAL ACTION INFORMATION", ""],
["get <JAIL> actionproperties <ACT>", "gets a list of properties for the action <ACT> for <JAIL>"],
["get <JAIL> actionmethods <ACT>", "gets a list of methods for the action <ACT> for <JAIL>"],
["get <JAIL> action <ACT> <PROPERTY>", "gets the value of <PROPERTY> for the action <ACT> for <JAIL>"],
]


##
# Prints the protocol in a "man" format. This is used for the
# "-h" output of fail2ban-client.

def printFormatted():
	INDENT=4
	MARGIN=41
	WIDTH=34
	firstHeading = False
	for m in protocol:
		if m[0] == '' and firstHeading:
			output("")
		firstHeading = True
		first = True
		if len(m[0]) >= MARGIN:
			m[1] = ' ' * WIDTH + m[1]
		for n in textwrap.wrap(m[1], WIDTH, drop_whitespace=False):
			if first:
				line = ' ' * INDENT + m[0] + ' ' * (MARGIN - len(m[0])) + n.strip()
				first = False
			else:
				line = ' ' * (INDENT + MARGIN) + n.strip()
			output(line)


##
# Prints the protocol in a "mediawiki" format.

def printWiki():
	firstHeading = False
	for m in protocol:
		if m[0] == '':
			if firstHeading:
				output("|}")
			__printWikiHeader(m[1], m[2])
			firstHeading = True
		else:
			output("|-")
			output("| <span style=\"white-space:nowrap;\"><tt>" + m[0] + "</tt></span> || || " + m[1])
	output("|}")


def __printWikiHeader(section, desc):
	output("")
	output("=== " + section + " ===")
	output("")
	output(desc)
	output("")
	output("{|")
	output("| '''Command''' || || '''Description'''")
