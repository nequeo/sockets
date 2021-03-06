// Warning 169 (Disables the 'Never used' warning)
#pragma warning disable 169
//------------------------------------------------------------------------------
// <auto-generated>
//     This code was generated by a tool.
//     Runtime Version:4.0.30319.1
//
//     Changes to this file may cause incorrect behavior and will be lost if
//     the code is regenerated.
// </auto-generated>
//------------------------------------------------------------------------------

namespace Nequeo.Net.Sockets
{
    using System;
    using System.Text;
    using System.Data;
    using System.Threading;
    using System.Diagnostics;
    using System.Data.SqlClient;
    using System.Data.OleDb;
    using System.Data.Odbc;
    using System.Collections;
    using System.Reflection;
    using System.Collections.Generic;
    using System.Xml.Serialization;
    using System.Runtime.Serialization;
    using System.ComponentModel;
    using System.Linq;
    using System.Linq.Expressions;
    
    #region Client Extension Type
    /// <summary>
    /// The Client object class.
    /// </summary>
    public partial class Client
    {
        private Exception _exceptionClient = null;
		private ClientAsync _asyncClientContext = null;

		/// <summary>
        /// Gets the current async exception; else null;
        /// </summary>
        public Exception ExceptionClient
        {
            get { return _exceptionClient; }
        }

		/// <summary>
        /// Gets the Client async context.
        /// </summary>
        public ClientAsync ClientAsyncContext
        {
            get { return _asyncClientContext; }
        }

		/// <summary>
        /// On create.
        /// </summary>
        partial void OnCreated();

		/// <summary>
        /// On create instance of Client
        /// </summary>
		partial void OnCreated()
		{
			// Start the async control.
			_asyncClientContext = new ClientAsync(this);
			_asyncClientContext.AsyncError += new Nequeo.Threading.EventHandler<Exception>(AsyncEvent_AsyncError);
		}

		/// <summary>
        /// Async error
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e1"></param>
        private void AsyncEvent_AsyncError(object sender, Exception e1)
        {
            _exceptionClient = e1;
        }

		/// <summary>
        /// Client async handler.
        /// </summary>
        public class ClientAsync : Nequeo.Threading.AsyncExecutionHandler<Client>
        {
            /// <summary>
            /// Client async handler.
            /// </summary>
            /// <param name="service">The Client type.</param>
            public ClientAsync(Client service)
                : base(service) { }
        }
    }
    #endregion
}

#pragma warning restore 169
