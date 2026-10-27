using System;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// Keeps a job that only looks at the drawing out of its undo history.
    ///
    /// A preview changes the page setup and puts it back; a list makes a
    /// scratch selection set. Each of those COM writes is an undo step of its
    /// own, so one Ctrl+Z after Claude looked at the drawing undid the look,
    /// not the modeller's last change (live check A30, 2026-10-27). While a
    /// Read job runs, the host turns undo recording off for the drawing. It
    /// comes back on at that job's end, or at the next job's begin if the end
    /// was lost. The host adds its own safety nets on top.
    ///
    /// The rules live here so they are tested offline; the host only switches.
    /// </summary>
    public sealed class UndoPause
    {
        private readonly object _gate = new object();
        private readonly Func<bool> _pause;
        private readonly Action _resume;
        private string? _job;

        /// <param name="pause">Turn recording off. True only when it was on and is now off.</param>
        /// <param name="resume">Turn back on what pause turned off. Safe to call twice.</param>
        public UndoPause(Func<bool> pause, Action resume)
        {
            _pause = pause;
            _resume = resume;
        }

        /// <summary>
        /// Read only. A View job (zoom, regen, switch drawing) keeps its undo
        /// step, the same as the modeller's own ZOOM does in AutoCAD.
        /// </summary>
        public static bool Applies(Risk risk) => risk == Risk.Read;

        /// <summary>The read job that has recording off, or null.</summary>
        public string? PausedFor
        {
            get
            {
                lock (_gate) return _job;
            }
        }

        public void Begin(JobInfo job)
        {
            lock (_gate)
            {
                // An end that never came must not leave the next job unrecorded.
                ResumeLocked();
                if (!Applies(job.Risk)) return;
                // Recording already off (UNDO Control None, or the pause could
                // not run): nothing to turn back on later.
                if (_pause()) _job = job.Job;
            }
        }

        public void End(string job)
        {
            lock (_gate)
            {
                if (_job == job) ResumeLocked();
            }
        }

        private void ResumeLocked()
        {
            if (_job == null) return;
            _job = null;
            _resume();
        }
    }
}
