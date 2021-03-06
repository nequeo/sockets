/* Company :       Nequeo Pty Ltd, http://www.nequeo.com.au/
*  Copyright :     Copyright � Nequeo Pty Ltd 2014 http://www.nequeo.com.au/
*
*  File :          RawSocketProvider.cpp
*  Purpose :       RawSocketProvider class.
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

#include "stdafx.h"

#include "RawSocketProvider.h"
#include "Exceptions\Exception.h"
#include "Exceptions\ExceptionCode.h"

using Nequeo::Exceptions::InvalidArgumentException;
using Nequeo::Net::Sockets::AddressFamily;

namespace Nequeo {
	namespace Net {
		namespace Provider
		{
			RawSocketProvider::RawSocketProvider()
			{
				init(AF_INET);
			}


			RawSocketProvider::RawSocketProvider(AddressFamily family, int proto)
			{
				if (family == AddressFamily::IPv4)
					init2(AF_INET, proto);
				else if (family == AddressFamily::IPv6)
					init2(AF_INET6, proto);
				else throw InvalidArgumentException("Invalid or unsupported address family passed to RawSocketImpl");
			}


			RawSocketProvider::RawSocketProvider(nequeo_socket_t sockfd) :
				SocketProvider(sockfd)
			{
			}


			RawSocketProvider::~RawSocketProvider()
			{
			}


			void RawSocketProvider::init(int af)
			{
				init2(af, IPPROTO_RAW);
			}


			void RawSocketProvider::init2(int af, int proto)
			{
				initSocket(af, SOCK_RAW, proto);
				setOption(IPPROTO_IP, IP_HDRINCL, 0);
			}
		}
	}
}