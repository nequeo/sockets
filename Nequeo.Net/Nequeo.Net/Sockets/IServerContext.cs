﻿/*  Company :       Nequeo Pty Ltd, http://www.nequeo.com.au/
 *  Copyright :     Copyright © Nequeo Pty Ltd 2010 http://www.nequeo.com.au/
 * 
 *  File :          
 *  Purpose :       
 * 
 */

#region Nequeo Pty Ltd License
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
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Net;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;

using Nequeo.Security;
using Nequeo.Threading;

namespace Nequeo.Net.Sockets
{
    /// <summary>
    /// General socket server context provider used for server client interface.
    /// </summary>
    public interface IServerContext
    {
        /// <summary>
        /// Gets, the unique identifier for this connection.
        /// </summary>
        string UniqueIdentifier { get; }

        /// <summary>
        /// Gets the current unique connection identifier.
        /// </summary>
        string ConnectionID { get; }

        /// <summary>
        /// Gets, the state descriptor of the current client server context.
        /// </summary>
        object State { get; }

        /// <summary>
        /// Gets, the current server name.
        /// </summary>
        string Name { get; }

        /// <summary>
        /// Get the client ip endpoint (remote end point).
        /// </summary>
        /// <returns>The client ip endpoint; else null.</returns>
        IPEndPoint GetClientIPEndPoint();

        /// <summary>
        /// Send data to the client through the server context from the server.
        /// </summary>
        /// <param name="data">The data received from the server.</param>
        /// <exception cref="System.ArgumentNullException"></exception>
        void SentFromServer(byte[] data);

        /// <summary>
        /// Get the last error that occured.
        /// </summary>
        /// <returns>The last exception.</returns>
        Exception GetLastError();

        /// <summary>
        /// Disconnect the current client and releases all resources.
        /// </summary>
        void Close();

        /// <summary>
        /// Has the current context timed out.
        /// </summary>
        /// <param name="timeout">The time out (minutes) set for the context; -1 wait indefinitely.</param>
        /// <returns>True if the context has timed out; else false.</returns>
        bool HasTimedOut(int timeout);

    }

    /// <summary>
    /// General socket server context provider used for server client interface.
    /// </summary>
    public interface IUdpServerContext
    {
        /// <summary>
        /// Gets, the unique identifier for this connection.
        /// </summary>
        string UniqueIdentifier { get; }

        /// <summary>
        /// Gets the current unique connection identifier.
        /// </summary>
        string ConnectionID { get; }

        /// <summary>
        /// Gets, the state descriptor of the current client server context.
        /// </summary>
        object State { get; }

        /// <summary>
        /// Gets, the current server name.
        /// </summary>
        string Name { get; }

        /// <summary>
        /// Get the client ip endpoint (remote end point).
        /// </summary>
        /// <returns>The client ip endpoint; else null.</returns>
        IPEndPoint GetClientIPEndPoint();

        /// <summary>
        /// Get the last error that occured.
        /// </summary>
        /// <returns>The last exception.</returns>
        Exception GetLastError();

        /// <summary>
        /// Disconnect the current client and releases all resources.
        /// </summary>
        void Close();

        /// <summary>
        /// Send data to the client through the server context from the server.
        /// </summary>
        /// <param name="data">The data received from the server.</param>
        /// <exception cref="System.ArgumentNullException"></exception>
        void SentFromServer(byte[] data);
        
    }
}
