using System;
using System.Collections.Concurrent;
using System.Windows.Threading;
using Heron.AutoCAD.Bridge;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// Gets work from a pipe thread onto AutoCAD's main thread.
    ///
    /// The AutoCAD API may only be touched from the main thread. Pipe threads
    /// queue work here, and AutoCAD's Idle event drains the queue; Idle only
    /// fires when AutoCAD waits for the user, never in the middle of a command.
    /// Idle fires when the message queue goes empty, so every Post also posts
    /// an empty message to the main thread: without it, queued work could wait
    /// for the next mouse move.
    /// </summary>
    internal static class IdleQueue
    {
        private static readonly ConcurrentQueue<Action> Work = new ConcurrentQueue<Action>();
        private static Dispatcher? _main;
        private static bool _hooked;

        /// <summary>Call once, on the main thread.</summary>
        public static void Hook()
        {
            if (_hooked) return;
            _main = Dispatcher.CurrentDispatcher;
            AcApp.Idle += OnIdle;
            _hooked = true;
        }

        public static void Unhook()
        {
            if (!_hooked) return;
            AcApp.Idle -= OnIdle;
            _hooked = false;
        }

        public static void Post(Action action)
        {
            Work.Enqueue(action);
            Wake();
        }

        /// <summary>
        /// Run on the main thread and wait up to <paramref name="timeout"/>. Work
        /// not started by then is abandoned and never runs later.
        /// </summary>
        public static bool TryInvoke<T>(Func<T> func, TimeSpan timeout, out T result)
        {
            var work = new OneShotWork<T>(func);
            Post(work.Run);
            var ok = work.Wait(timeout, out result);
            if (work.Error != null) HeronLog.Error("Main-thread work failed", work.Error);
            return ok;
        }

        private static void Wake()
        {
            try
            {
                _main?.BeginInvoke(DispatcherPriority.Background, new Action(() => { }));
            }
            catch (Exception ex)
            {
                HeronLog.Error("Wake the main thread", ex);
            }
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
            if (!Work.IsEmpty) Wake();
        }
    }
}
