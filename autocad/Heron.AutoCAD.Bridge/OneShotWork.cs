using System;
using System.Threading;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// Work handed from a pipe thread to AutoCAD's main thread, run at most once.
    ///
    /// If the pipe thread stops waiting before the main thread gets to it, the
    /// work is abandoned and will not run later: a Keep or Discard box must
    /// never pop up after the chat has already moved on.
    /// </summary>
    public sealed class OneShotWork<T>
    {
        private const int Waiting = 0, Running = 1, Abandoned = 2;
        private readonly Func<T> _func;
        private readonly ManualResetEventSlim _done = new ManualResetEventSlim(false);
        private int _state;
        private T _result = default!;

        public OneShotWork(Func<T> func) => _func = func;

        public Exception? Error { get; private set; }

        /// <summary>Main thread. Does nothing if the caller already gave up.</summary>
        public void Run()
        {
            if (Interlocked.CompareExchange(ref _state, Running, Waiting) != Waiting) return;
            try
            {
                _result = _func();
            }
            catch (Exception ex)
            {
                Error = ex;
            }
            finally
            {
                _done.Set();
            }
        }

        /// <summary>
        /// Pipe thread. True with the result when it ran in time and did not
        /// throw. Not started in time: abandoned, false. Already running: waits
        /// for it to finish (the work enforces its own deadline).
        /// </summary>
        public bool Wait(TimeSpan timeout, out T result)
        {
            result = default!;
            if (!_done.Wait(timeout))
            {
                if (Interlocked.CompareExchange(ref _state, Abandoned, Waiting) == Waiting) return false;
                _done.Wait();
            }
            if (Error != null) return false;
            result = _result;
            return true;
        }
    }
}
