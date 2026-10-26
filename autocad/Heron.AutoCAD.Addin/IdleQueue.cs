using System;
using System.Collections.Concurrent;
using System.Threading;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// Gets work from a pipe thread onto AutoCAD's main thread.
    ///
    /// The AutoCAD API may only be touched from the main thread. The pipe
    /// threads queue work here, and AutoCAD's Idle event drains the queue,
    /// which only fires when AutoCAD is waiting for the user: never in the
    /// middle of a command. Work that changes anything locks the document
    /// itself.
    /// </summary>
    internal static class IdleQueue
    {
        private static readonly ConcurrentQueue<Action> Work = new ConcurrentQueue<Action>();
        private static bool _hooked;

        /// <summary>Call once, on the main thread.</summary>
        public static void Hook()
        {
            if (_hooked) return;
            AcApp.Idle += OnIdle;
            _hooked = true;
        }

        public static void Unhook()
        {
            if (!_hooked) return;
            AcApp.Idle -= OnIdle;
            _hooked = false;
        }

        public static void Post(Action action) => Work.Enqueue(action);

        /// <summary>Run on the main thread and wait for the result, up to <paramref name="timeout"/>.</summary>
        public static bool TryInvoke<T>(Func<T> func, TimeSpan timeout, out T result)
        {
            var done = new ManualResetEventSlim(false);
            var value = default(T)!;
            Exception? error = null;
            Work.Enqueue(() =>
            {
                try
                {
                    value = func();
                }
                catch (Exception ex)
                {
                    error = ex;
                }
                finally
                {
                    done.Set();
                }
            });
            var finished = done.Wait(timeout);
            result = value;
            if (error != null) HeronLog.Error("Main-thread work failed", error);
            return finished && error == null;
        }

        private static void OnIdle(object? sender, EventArgs e)
        {
            // A few per Idle so a burst never makes AutoCAD feel stuck.
            for (var i = 0; i < 8 && Work.TryDequeue(out var action); i++)
            {
                try
                {
                    action();
                }
                catch (Exception ex)
                {
                    HeronLog.Error("Idle work failed", ex);
                }
            }
        }
    }
}
