using System;
using System.Collections.Generic;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// Treats a double-click on a ribbon switch as one click. Modellers
    /// double-click out of habit; without this a padlock flips on and straight
    /// back off (seen live 2026-10-26: 0.4 s and 0.86 s between the two clicks).
    /// </summary>
    public sealed class RepeatClickFilter
    {
        public static readonly TimeSpan Window = TimeSpan.FromMilliseconds(1500);
        private readonly Dictionary<string, DateTime> _last = new Dictionary<string, DateTime>();
        private readonly object _gate = new object();

        /// <summary>True when this click should act; false for the echo of a double-click.</summary>
        public bool Accept(string button, DateTime now)
        {
            lock (_gate)
            {
                if (_last.TryGetValue(button, out var previous) && now - previous < Window) return false;
                _last[button] = now;
                return true;
            }
        }
    }
}
