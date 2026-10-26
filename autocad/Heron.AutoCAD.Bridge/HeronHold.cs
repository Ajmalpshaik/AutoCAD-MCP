using System;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// One chat at a time per AutoCAD. The hold frees itself after three quiet
    /// minutes, on release, or on disconnect (each connect gets a new hold).
    /// </summary>
    public sealed class HeronHold
    {
        public static readonly TimeSpan Idle = TimeSpan.FromMinutes(3);
        private readonly object _gate = new object();
        private string? _holder;
        private DateTime _last;

        public bool TryTake(string conversation, DateTime now)
        {
            lock (_gate)
            {
                if (_holder == null || _holder == conversation || now - _last >= Idle)
                {
                    _holder = conversation;
                    _last = now;
                    return true;
                }
                return false;
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
