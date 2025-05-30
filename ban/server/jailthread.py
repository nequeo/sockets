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

import sys
from threading import Thread
from abc import abstractmethod

from .utils import Utils
from ..helpers import excepthook, prctl_set_th_name


class JailThread(Thread):
	"""Abstract class for threading elements in Fail2Ban.

	Attributes
	----------
	daemon
	ident
	name
	status
	active : bool
		Control the state of the thread.
	idle : bool
		Control the idle state of the thread.
	sleeptime : int
		The time the thread sleeps for in the loop.
	"""

	def __init__(self, name=None):
		super(JailThread, self).__init__(name=name)
		## Should going with main thread also:
		self.daemon = True
		## Control the state of the thread (None - was not started, True - active, False - stopped).
		self.active = None
		## Control the idle state of the thread.
		self.idle = False
		## The time the thread sleeps in the loop.
		self.sleeptime = Utils.DEFAULT_SLEEP_TIME

		# excepthook workaround for threads, derived from:
		# http://bugs.python.org/issue1230540#msg91244
		run = self.run

		def run_with_except_hook(*args, **kwargs):
			try:
				run(*args, **kwargs)
				# call on stop callback to do some finalizations:
				self.onStop()
			except Exception as e:
				# avoid very sporadic error "'NoneType' object has no attribute 'exc_info'" (https://bugs.python.org/issue7336)
				# only extremely fast systems are affected ATM (2.7 / 3.x), if thread ends nothing is available here.
				if sys is not None:
					excepthook(*sys.exc_info())
				else:
					print(e)
		self.run = run_with_except_hook

	def _bootstrap(self):
		prctl_set_th_name(self.name)
		return super(JailThread, self)._bootstrap();

	@abstractmethod
	def status(self, flavor="basic"): # pragma: no cover - abstract
		"""Abstract - Should provide status information.
		"""
		pass

	def start(self):
		"""Sets active flag and starts thread.
		"""
		self.active = True
		super(JailThread, self).start()

	@abstractmethod
	def onStop(self): # pragma: no cover - absract
		"""Abstract - Called when thread ends (after run).
		"""
		pass

	def stop(self):
		"""Sets `active` property to False, to flag run method to return.
		"""
		if self.active: self.active = False
		# normally onStop will be called automatically in thread after its run ends,
		# but for backwards compatibilities we'll invoke it in caller of stop method.
		self.onStop()
		self.onStop = lambda:()
		self.done()

	def done(self):
		self.done = lambda:()
		# if still runniung - wait a bit before initiate clean-up:
		if self.is_alive():
			Utils.wait_for(lambda: not self.is_alive(), 5)
		# now clean-up everything:
		self.afterStop()


	@abstractmethod
	def run(self): # pragma: no cover - absract
		"""Abstract - Called when thread starts, thread stops when returns.
		"""
		pass

	def afterStop(self):
		"""Cleanup resources."""
		pass

	def join(self):
		""" Safer join, that could be called also for not started (or ended) threads (used for cleanup).
		"""
		## if cleanup needed - create derivative and call it before join...
		self.done()
		## if was really started - should call join:
		if self.active is not None:
			super(JailThread, self).join()

## python 3.9, restore isAlive method:
if not hasattr(JailThread, 'isAlive'):
	 JailThread.isAlive = JailThread.is_alive
