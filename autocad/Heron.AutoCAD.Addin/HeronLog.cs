using System;
using System.IO;
using System.Threading;

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// The add-in's own log, one file per day under
    /// %LOCALAPPDATA%\Heron\autocad\logs. Logging never throws.
    /// </summary>
    internal static class HeronLog
    {
        private static readonly object Gate = new object();

        public static string Folder => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Heron", "autocad", "logs");

        public static string TodayPath => Path.Combine(Folder, "addin-" + DateTime.UtcNow.ToString("yyyyMMdd") + ".log");

        public static void Write(string message)
        {
            try
            {
                lock (Gate)
                {
                    Directory.CreateDirectory(Folder);
                    File.AppendAllText(TodayPath,
                        DateTime.UtcNow.ToString("HH:mm:ss.fff") + " [" + Thread.CurrentThread.ManagedThreadId + "] " + message + Environment.NewLine);
                }
            }
            catch (Exception)
            {
            }
        }

        public static void Error(string what, Exception ex) => Write(what + ": " + ex);
    }
}
