using System;
using System.Windows.Threading;
using Autodesk.AutoCAD.Runtime;
using Heron.AutoCAD.Bridge;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

[assembly: ExtensionApplication(typeof(Heron.AutoCAD.Addin.HeronApplication))]

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// Heron AI for AutoCAD, loaded by AutoCAD from HeronAutoCAD.bundle.
    ///
    /// AutoCAD starts disconnected: a session nobody connected is invisible
    /// to every chat. Pressing Heron (or typing HERON) connects it.
    /// </summary>
    public sealed class HeronApplication : IExtensionApplication
    {
        private DispatcherTimer? _refresh;

        internal static BridgeServer? Server { get; private set; }
        internal static string AcadVersion { get; private set; } = "";
        internal static string AddinVersion { get; } = typeof(HeronApplication).Assembly.GetName().Version?.ToString(3) ?? "";
        internal static string? StartError { get; private set; }

        internal static HeronConfig LoadConfig() => HeronConfig.Load(HeronConfig.DefaultPath);

        public void Initialize()
        {
            try
            {
                AcadVersion = Convert.ToString(AcApp.GetSystemVariable("ACADVER")) ?? "";
                var banner = new HeronActivityBanner(AcApp.MainWindow.Handle);
                Server = new BridgeServer(new AcadJobHost(banner, LoadConfig), LoadConfig, AcadVersion, AddinVersion);
                IdleQueue.Hook();
                HeronRibbon.Init();
                AcApp.QuitWillStart += (s, e) => Server?.Stop();

                // Pick up padlocks changed in another AutoCAD, and the
                // "Keep: rest of job" label running out.
                _refresh = new DispatcherTimer { Interval = TimeSpan.FromSeconds(15) };
                _refresh.Tick += (s, e) => HeronRibbon.Repaint();
                _refresh.Start();

                if (LoadConfig().AutoConnect) HeronActions.ToggleConnect();
                HeronLog.Write("Heron for AutoCAD " + AddinVersion + " loaded in AutoCAD " + AcadVersion + ".");
            }
            catch (System.Exception ex)
            {
                StartError = "Heron did not start: " + ex.Message;
                HeronLog.Error("Initialize", ex);
            }
        }

        public void Terminate()
        {
            try
            {
                _refresh?.Stop();
                Server?.Stop();
                IdleQueue.Unhook();
            }
            catch (System.Exception ex)
            {
                HeronLog.Error("Terminate", ex);
            }
        }
    }
}
