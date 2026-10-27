using System;
using System.Windows.Threading;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// Turns undo recording off for the active drawing while a read job runs,
    /// and back on after (the rules are in Bridge's UndoPause). Pause and
    /// Resume are called on pipe threads; the drawing is touched on the main
    /// thread only.
    ///
    /// Recording off for longer than a read would cost the modeller their own
    /// Ctrl+Z, so besides the job's end there are three safety nets: the
    /// modeller starting a command, the drawing closing, and a deadline.
    /// </summary>
    internal static class UndoSwitch
    {
        private static readonly TimeSpan PauseWait = TimeSpan.FromSeconds(2);
        private static readonly TimeSpan ResumeWait = TimeSpan.FromSeconds(5);
        // Longer than any read should take; a read still running then simply
        // records its last steps, as before.
        private static readonly TimeSpan Deadline = TimeSpan.FromMinutes(2);

        // Main thread only.
        private static Document? _doc;
        private static Database? _db;
        private static DispatcherTimer? _deadline;

        /// <summary>Pipe thread. True only when recording was on and is now off.</summary>
        public static bool Pause()
        {
            var ran = IdleQueue.TryInvoke(PauseHere, PauseWait, out var paused);
            return ran && paused;
        }

        /// <summary>Any thread. Waits, so the next job never starts with recording off.</summary>
        public static void Resume()
        {
            if (IdleQueue.OnMainThread)
            {
                ResumeHere("end");
                return;
            }
            if (!IdleQueue.TryInvoke(() => { ResumeHere("end"); return true; }, ResumeWait, out _))
                IdleQueue.Post(() => ResumeHere("late end"));
        }

        private static bool PauseHere()
        {
            ResumeHere("new pause");
            var doc = AcApp.DocumentManager.MdiActiveDocument;
            var db = doc?.Database;
            if (doc == null || db == null || !db.UndoRecording) return false;
            db.DisableUndoRecording(true);
            _doc = doc;
            _db = db;
            doc.CommandWillStart += OnCommandWillStart;
            AcApp.DocumentManager.DocumentToBeDestroyed += OnDocumentToBeDestroyed;
            _deadline = new DispatcherTimer { Interval = Deadline };
            _deadline.Tick += (s, e) => ResumeHere("deadline");
            _deadline.Start();
            HeronLog.Write("undo paused for a read on " + doc.Name);
            return true;
        }

        /// <summary>Main thread. Does nothing when nothing is paused.</summary>
        private static void ResumeHere(string why)
        {
            var db = _db;
            var doc = _doc;
            if (db == null) return;
            _db = null;
            _doc = null;
            _deadline?.Stop();
            _deadline = null;
            AcApp.DocumentManager.DocumentToBeDestroyed -= OnDocumentToBeDestroyed;
            try
            {
                if (doc != null) doc.CommandWillStart -= OnCommandWillStart;
                if (!db.IsDisposed) db.DisableUndoRecording(false);
                HeronLog.Write("undo resumed (" + why + ")");
            }
            catch (Exception ex)
            {
                HeronLog.Error("Turn undo back on", ex);
            }
        }

        private static void OnCommandWillStart(object sender, CommandEventArgs e)
        {
            // A preview's PlotToFile may run as PLOT: that is the read itself,
            // not the modeller starting work.
            if (e.GlobalCommandName.IndexOf("PLOT", StringComparison.OrdinalIgnoreCase) >= 0) return;
            ResumeHere("command " + e.GlobalCommandName);
        }

        private static void OnDocumentToBeDestroyed(object sender, DocumentCollectionEventArgs e)
        {
            if (e.Document == _doc) ResumeHere("drawing closing");
        }
    }
}
