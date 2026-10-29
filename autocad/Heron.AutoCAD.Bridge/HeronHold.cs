using System;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// One chat at a time per AutoCAD. The hold frees itself after three quiet
    /// minutes, on release, or on disconnect (each connect gets a new hold).
    /// While the holder's operation runs in the plug-in it is pinned: a long
    /// shell or super hatch is not "quiet", however long it takes.
    /// </summary>
    public sealed class HeronHold
    {
        public static readonly TimeSpan Idle = TimeSpan.FromMinutes(3);
        private readonly object _gate = new object();
        private string? _holder;
        private DateTime _last;
        private int _pinned;

        public bool TryTake(string conversation, DateTime now)
        {
            lock (_gate)
            {
                if (_holder == null || _holder == conversation || (_pinned == 0 && now - _last >= Idle))
                {
                    _holder = conversation;
                    _last = now;
                    return true;
                }
                return false;
            }
        }

        /// <summary>Take the hold for an operation and keep it until <see cref="Unpin"/>.</summary>
        public bool TryPin(string conversation, DateTime now)
        {
            lock (_gate)
            {
                if (!TryTake(conversation, now)) return false;
                _pinned++;
                return true;
            }
        }

        /// <summary>The operation finished: quiet time counts from now.</summary>
        public void Unpin(DateTime now)
        {
            lock (_gate)
            {
                if (_pinned > 0) _pinned--;
                _last = now;
            }
        }

        public void Release(string conversation)
        {
            lock (_gate)
            {
                if (_holder == conversation) _holder = null;
            }
        }

        public string? Holder
        {
            get { lock (_gate) return _holder; }
        }
    }
}
