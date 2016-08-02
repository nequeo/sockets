/* Company :       Nequeo Pty Ltd, http://www.nequeo.com.au/
*  Copyright :     Copyright � Nequeo Pty Ltd 2014 http://www.nequeo.com.au/
*
*  File :          IPAddress.h
*  Purpose :       IPAddress class.
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

#ifndef _IPADDRESS_H
#define _IPADDRESS_H

#include "GlobalSocket.h"
#include "AddressFamily.h"
#include "Base\Types.h"
#include "IPv4AddressProvider.h"
#include "IPv6AddressProvider.h"

using Nequeo::UInt8;
using Nequeo::UInt16;
using Nequeo::UInt32;

namespace Nequeo {
	namespace Net {
		namespace Sockets
		{
			// Include the IP Address provider.
			class IPAddressProvider;

			/// This class represents an internet (IP) host
			/// address. The address can belong either to the
			/// IPv4 or the IPv6 address family.
			///
			/// Relational operators (==, !=, <, <=, >, >=) are
			/// supported. However, you must not interpret any
			/// special meaning into the result of these 
			/// operations, other than that the results are
			/// consistent.
			///
			/// Especially, an IPv4 address is never equal to
			/// an IPv6 address, even if the IPv6 address is
			/// IPv4 compatible and the addresses are the same.
			///
			/// IPv6 addresses are supported only if the target platform
			/// supports IPv6.
			class IPAddress
			{
			public:
				
				IPAddress();
				/// Creates a wildcard (zero) IPv4 IPAddress.

				IPAddress(const IPAddress& addr);
				/// Creates an IPAddress by copying another one.

				explicit IPAddress(Nequeo::Net::Sockets::AddressFamily addressFamily);
				/// Creates a wildcard (zero) IPAddress for the
				/// given address family.

				explicit IPAddress(const std::string& addr);
				/// Creates an IPAddress from the string containing
				/// an IP address in presentation format (dotted decimal
				/// for IPv4, hex string for IPv6).
				/// 
				/// Depending on the format of addr, either an IPv4 or
				/// an IPv6 address is created.
				///
				/// See toString() for details on the supported formats.
				///
				/// Throws an InvalidAddressException if the address cannot be parsed.

				IPAddress(const std::string& addr, Nequeo::Net::Sockets::AddressFamily addressFamily);
				/// Creates an IPAddress from the string containing
				/// an IP address in presentation format (dotted decimal
				/// for IPv4, hex string for IPv6).

				IPAddress(const void* addr, nequeo_socklen_t length);
				/// Creates an IPAddress from a native internet address.
				/// A pointer to a in_addr or a in6_addr structure may be 
				/// passed.

				IPAddress(const void* addr, nequeo_socklen_t length, UInt32 scope);
				/// Creates an IPAddress from a native internet address.
				/// A pointer to a in_addr or a in6_addr structure may be 
				/// passed. Additionally, for an IPv6 address, a scope ID
				/// may be specified. The scope ID will be ignored if an IPv4
				/// address is specified.

				~IPAddress();
				/// Destroys the IPAddress.

				IPAddress& operator = (const IPAddress& addr);
				/// Assigns an IPAddress.

				void swap(IPAddress& address);
				/// Swaps the IPAddress with another one.

				Nequeo::Net::Sockets::AddressFamily addressFamily() const;
				/// Returns the address family (IPv4 or IPv6) of the address.

				UInt32 scope() const;
				/// Returns the IPv6 scope identifier of the address. Returns 0 if
				/// the address is an IPv4 address, or the address is an
				/// IPv6 address but does not have a scope identifier.

				std::string toString() const;
				/// Returns a string containing a representation of the address
				/// in presentation format.
				///
				/// For IPv4 addresses the result will be in dotted-decimal
				/// (d.d.d.d) notation.
				///
				/// Textual representation of IPv6 address is one of the following forms:
				///
				/// The preferred form is x:x:x:x:x:x:x:x, where the 'x's are the hexadecimal 
				/// values of the eight 16-bit pieces of the address. This is the full form.
				/// Example: 1080:0:0:0:8:600:200A:425C
				///
				/// It is not necessary to write the leading zeros in an individual field. 
				/// However, there must be at least one numeral in every field, except as described below.
				/// 
				/// It is common for IPv6 addresses to contain long strings of zero bits. 
				/// In order to make writing addresses containing zero bits easier, a special syntax is 
				/// available to compress the zeros. The use of "::" indicates multiple groups of 16-bits of zeros. 
				/// The "::" can only appear once in an address. The "::" can also be used to compress the leading 
				/// and/or trailing zeros in an address. Example: 1080::8:600:200A:425C
				///
				/// For dealing with IPv4 compatible addresses in a mixed environment,
				/// a special syntax is available: x:x:x:x:x:x:d.d.d.d, where the 'x's are the 
				/// hexadecimal values of the six high-order 16-bit pieces of the address, 
				/// and the 'd's are the decimal values of the four low-order 8-bit pieces of the 
				/// standard IPv4 representation address. Example: ::FFFF:192.168.1.120
				///
				/// If an IPv6 address contains a non-zero scope identifier, it is added
				/// to the string, delimited by a percent character. On Windows platforms,
				/// the numeric value (which specifies an interface index) is directly
				/// appended. On Unix platforms, the name of the interface corresponding
				/// to the index (interpretation of the scope identifier) is added.

				bool isWildcard() const;
				/// Returns true iff the address is a wildcard (all zero)
				/// address.

				bool isBroadcast() const;
				/// Returns true iff the address is a broadcast address.
				///
				/// Only IPv4 addresses can be broadcast addresses. In a broadcast
				/// address, all bits are one.
				///
				/// For a IPv6 address, returns always false.

				bool isLoopback() const;
				/// Returns true iff the address is a loopback address.
				///
				/// For IPv4, the loopback address is 127.0.0.1.
				///
				/// For IPv6, the loopback address is ::1.

				bool isMulticast() const;
				/// Returns true iff the address is a multicast address.
				///
				/// IPv4 multicast addresses are in the
				/// 224.0.0.0 to 239.255.255.255 range
				/// (the first four bits have the value 1110).
				///
				/// IPv6 multicast addresses are in the
				/// FFxx:x:x:x:x:x:x:x range.

				bool isUnicast() const;
				/// Returns true iff the address is a unicast address.
				///
				/// An address is unicast if it is neither a wildcard,
				/// broadcast or multicast address.

				bool isLinkLocal() const;
				/// Returns true iff the address is a link local unicast address.
				///
				/// IPv4 link local addresses are in the 169.254.0.0/16 range,
				/// according to RFC 3927.
				///
				/// IPv6 link local addresses have 1111 1110 10 as the first
				/// 10 bits, followed by 54 zeros.

				bool isSiteLocal() const;
				/// Returns true iff the address is a site local unicast address.
				///
				/// IPv4 site local addresses are in on of the 10.0.0.0/24,
				/// 192.168.0.0/16 or 172.16.0.0 to 172.31.255.255 ranges.
				///
				/// IPv6 site local addresses have 1111 1110 11 as the first
				/// 10 bits, followed by 38 zeros.

				bool isIPv4Compatible() const;
				/// Returns true iff the address is IPv4 compatible.
				///
				/// For IPv4 addresses, this is always true.
				///
				/// For IPv6, the address must be in the ::x:x range (the
				/// first 96 bits are zero).

				bool isIPv4Mapped() const;
				/// Returns true iff the address is an IPv4 mapped IPv6 address.
				///
				/// For IPv4 addresses, this is always true.
				///
				/// For IPv6, the address must be in the ::FFFF:x:x range.

				bool isWellKnownMC() const;
				/// Returns true iff the address is a well-known multicast address.
				///
				/// For IPv4, well-known multicast addresses are in the 
				/// 224.0.0.0/8 range.
				///
				/// For IPv6, well-known multicast addresses are in the 
				/// FF0x:x:x:x:x:x:x:x range.

				bool isNodeLocalMC() const;
				/// Returns true iff the address is a node-local multicast address.
				///
				/// IPv4 does not support node-local addresses, thus the result is
				/// always false for an IPv4 address.
				///
				/// For IPv6, node-local multicast addresses are in the
				/// FFx1:x:x:x:x:x:x:x range.

				bool isLinkLocalMC() const;
				/// Returns true iff the address is a link-local multicast address.
				///
				/// For IPv4, link-local multicast addresses are in the
				/// 224.0.0.0/24 range. Note that this overlaps with the range for well-known
				/// multicast addresses.
				///
				/// For IPv6, link-local multicast addresses are in the
				/// FFx2:x:x:x:x:x:x:x range.

				bool isSiteLocalMC() const;
				/// Returns true iff the address is a site-local multicast address.
				///
				/// For IPv4, site local multicast addresses are in the
				/// 239.255.0.0/16 range.
				///
				/// For IPv6, site-local multicast addresses are in the
				/// FFx5:x:x:x:x:x:x:x range.

				bool isOrgLocalMC() const;
				/// Returns true iff the address is a organization-local multicast address.
				///
				/// For IPv4, organization-local multicast addresses are in the
				/// 239.192.0.0/16 range.
				///
				/// For IPv6, organization-local multicast addresses are in the
				/// FFx8:x:x:x:x:x:x:x range.

				bool isGlobalMC() const;
				/// Returns true iff the address is a global multicast address.
				///
				/// For IPv4, global multicast addresses are in the 
				/// 224.0.1.0 to 238.255.255.255 range.
				///
				/// For IPv6, global multicast addresses are in the
				/// FFxF:x:x:x:x:x:x:x range.

				bool operator == (const IPAddress& addr) const;
				bool operator != (const IPAddress& addr) const;
				bool operator <  (const IPAddress& addr) const;
				bool operator <= (const IPAddress& addr) const;
				bool operator >  (const IPAddress& addr) const;
				bool operator >= (const IPAddress& addr) const;

				nequeo_socklen_t length() const;
				/// Returns the length in bytes of the internal socket address structure.	

				const void* addr() const;
				/// Returns the internal address structure.

				int af() const;
				/// Returns the address family (AF_INET or AF_INET6) of the address.

				void mask(const IPAddress& mask);
				/// Masks the IP address using the given netmask, which is usually
				/// a IPv4 subnet mask. Only supported for IPv4 addresses.
				///
				/// The new address is (address & mask).

				void mask(const IPAddress& mask, const IPAddress& set);
				/// Masks the IP address using the given netmask, which is usually
				/// a IPv4 subnet mask. Only supported for IPv4 addresses.
				///
				/// The new address is (address & mask) | (set & ~mask).

				static IPAddress parse(const std::string& addr);
				/// Creates an IPAddress from the string containing
				/// an IP address in presentation format (dotted decimal
				/// for IPv4, hex string for IPv6).
				/// 
				/// Depending on the format of addr, either an IPv4 or
				/// an IPv6 address is created.
				///
				/// See toString() for details on the supported formats.
				///
				/// Throws an InvalidAddressException if the address cannot be parsed.

				static bool tryParse(const std::string& addr, IPAddress& result);
				/// Tries to interpret the given address string as an
				/// IP address in presentation format (dotted decimal
				/// for IPv4, hex string for IPv6).
				///
				/// Returns true and stores the IPAddress in result if the
				/// string contains a valid address.
				///
				/// Returns false and leaves result unchanged otherwise.

				static IPAddress wildcard(Nequeo::Net::Sockets::AddressFamily addressFamily = IPv4);
				/// Returns a wildcard IPv4 or IPv6 address (0.0.0.0).

				static IPAddress broadcast();
				/// Returns a broadcast IPv4 address (255.255.255.255).

			protected:
				void init(IPAddressProvider* pImpl);

			private:
				bool _disposed;
				IPAddressProvider* _pImpl;
			};
		}
	}
}
#endif