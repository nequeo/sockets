/* Company :       Nequeo Pty Ltd, http://www.nequeo.com.au/
*  Copyright :     Copyright � Nequeo Pty Ltd 2014 http://www.nequeo.com.au/
*
*  File :          AddressFamily.h
*  Purpose :       AddressFamily enum.
*
*/

/*
	Permission is hereby granted, free of charge, to any person
	obtaining a copy of this software and associated documentation
	files (the "Software"), to deal in the Software without
	restriction, including without limitation the rights to use,
	copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the
	Software is furnished to do so, subject to the following
	conditions:

	The above copyright notice and this permission notice shall be
	included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
	OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
	OTHER DEALINGS IN THE SOFTWARE.
*/

#pragma once

#ifndef _ADDRESSFAMILY_H
#define _ADDRESSFAMILY_H

#include "GlobalSocket.h"

namespace Nequeo {
	namespace Net {
		namespace Sockets
		{
			// AddressFamily possible address families for IP addresses.
			enum AddressFamily
			{
				IPv4 = 1,
				IPv6 = 2
			};

			// The maximum address length.
			enum AddressLength
			{
				IPv4Length = IPv4_Length,
				IPv6Length = IPv6_Length
			};

			// The IP version.
			enum IPVersion
			{
				IPv4_ONLY,    /// Return interfaces with IPv4 address only
				IPv6_ONLY,    /// Return interfaces with IPv6 address only
				IPv4_OR_IPv6  /// Return interfaces with IPv4 or IPv6 address
			};
		}
	}
}
#endif