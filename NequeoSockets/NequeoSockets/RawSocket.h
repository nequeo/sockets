/* Company :       Nequeo Pty Ltd, http://www.nequeo.com.au/
*  Copyright :     Copyright � Nequeo Pty Ltd 2014 http://www.nequeo.com.au/
*
*  File :          RawSocket.h
*  Purpose :       RawSocket class.
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

#ifndef _RAWSOCKET_H
#define _RAWSOCKET_H

#include "GlobalSocket.h"
#include "Socket.h"
#include "AddressFamily.h"

using Nequeo::Net::Sockets::Socket;
using Nequeo::Net::Sockets::SocketAddress;
using Nequeo::Net::Sockets::SocketProvider;

namespace Nequeo {
	namespace Net {
		namespace Provider
		{
			/// This class provides an interface to a
			/// raw IP socket.
			class RawSocket : public Socket
			{
			public:
				RawSocket();
				/// Creates an unconnected IPv4 raw socket.

				RawSocket(Nequeo::Net::Sockets::AddressFamily family, int proto = IPPROTO_RAW);
				/// Creates an unconnected raw socket.
				///
				/// The socket will be created for the
				/// given address family.

				RawSocket(const SocketAddress& address, bool reuseAddress = false);
				/// Creates a raw socket and binds it
				/// to the given address.
				///
				/// Depending on the address family, the socket
				/// will be either an IPv4 or an IPv6 socket.

				RawSocket(const Socket& socket);
				/// Creates the RawSocket with the SocketImpl
				/// from another socket. The SocketImpl must be
				/// a RawSocketImpl, otherwise an InvalidArgumentException
				/// will be thrown.

				~RawSocket();
				/// Destroys the RawSocket.

				RawSocket& operator = (const Socket& socket);
				/// Assignment operator.
				///
				/// Releases the socket's SocketImpl and
				/// attaches the SocketImpl from the other socket and
				/// increments the reference count of the SocketImpl.	

				void connect(const SocketAddress& address);
				/// Restricts incoming and outgoing
				/// packets to the specified address.
				///
				/// Cannot be used together with bind().

				void bind(const SocketAddress& address, bool reuseAddress = false);
				/// Bind a local address to the socket.
				///
				/// This is usually only done when establishing a server
				/// socket. 
				///
				/// If reuseAddress is true, sets the SO_REUSEADDR
				/// socket option.
				///
				/// Cannot be used together with connect().

				int sendBytes(const void* buffer, int length, int flags = 0);
				/// Sends the contents of the given buffer through
				/// the socket.
				///
				/// Returns the number of bytes sent, which may be
				/// less than the number of bytes specified.

				int receiveBytes(void* buffer, int length, int flags = 0);
				/// Receives data from the socket and stores it
				/// in buffer. Up to length bytes are received.
				///
				/// Returns the number of bytes received.

				int sendTo(const void* buffer, int length, const SocketAddress& address, int flags = 0);
				/// Sends the contents of the given buffer through
				/// the socket to the given address.
				///
				/// Returns the number of bytes sent, which may be
				/// less than the number of bytes specified.

				int receiveFrom(void* buffer, int length, SocketAddress& address, int flags = 0);
				/// Receives data from the socket and stores it
				/// in buffer. Up to length bytes are received.
				/// Stores the address of the sender in address.
				///
				/// Returns the number of bytes received.

				void setBroadcast(bool flag);
				/// Sets the value of the SO_BROADCAST socket option.
				///
				/// Setting this flag allows sending datagrams to
				/// the broadcast address.

				bool getBroadcast() const;
				/// Returns the value of the SO_BROADCAST socket option.

			protected:
				RawSocket(SocketProvider* pImpl);
				/// Creates the Socket and attaches the given SocketImpl.
				/// The socket takes owership of the SocketImpl.
				///
				/// The SocketImpl must be a StreamSocketImpl, otherwise
				/// an InvalidArgumentException will be thrown.
			};


			//
			// inlines
			//
			inline void RawSocket::setBroadcast(bool flag)
			{
				impl()->setBroadcast(flag);
			}


			inline bool RawSocket::getBroadcast() const
			{
				return impl()->getBroadcast();
			}
		}
	}
}
#endif