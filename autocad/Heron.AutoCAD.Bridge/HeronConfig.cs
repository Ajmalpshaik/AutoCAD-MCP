using System;
using System.IO;
using System.Text;
using System.Text.Json;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// The padlocks and switches, in %APPDATA%\Heron\autocad\heron-autocad.config.
    /// Read fresh for every job. A file that cannot be read cleanly keeps every
    /// padlock off: failing closed is the only safe way to fail here.
    /// </summary>
    public sealed class HeronConfig
    {
        public bool WriteEnabled { get; set; }
        public bool PublishEnabled { get; set; }
        public bool AdminEnabled { get; set; }
        public bool AskBeforeKeeping { get; set; }
        public bool AutoConnect { get; set; }
        public bool ActivityBanner { get; set; } = true;

        public static string DefaultPath =>
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Heron", "autocad", "heron-autocad.config");

        public static HeronConfig Load(string path)
        {
            string text;
            try
            {
                if (!File.Exists(path)) return new HeronConfig();
                text = File.ReadAllText(path, Encoding.UTF8);
            }
            catch (Exception) { return new HeronConfig(); }

            try
            {
                using (var doc = JsonDocument.Parse(text))
                {
                    if (doc.RootElement.ValueKind != JsonValueKind.Object) return new HeronConfig();
                    var read = new HeronConfig();
                    foreach (var property in doc.RootElement.EnumerateObject())
                    {
                        var kind = property.Value.ValueKind;
                        if (kind != JsonValueKind.True && kind != JsonValueKind.False) return new HeronConfig();
                        var on = kind == JsonValueKind.True;
                        switch (property.Name)
                        {
                            case "write.enabled": read.WriteEnabled = on; break;
                            case "publish.enabled": read.PublishEnabled = on; break;
                            case "admin.enabled": read.AdminEnabled = on; break;
                            case "write.askBeforeKeeping": read.AskBeforeKeeping = on; break;
                            case "bridge.autoConnect": read.AutoConnect = on; break;
                            case "ui.activityBanner": read.ActivityBanner = on; break;
                        }
                    }
                    return read;
                }
            }
            catch (JsonException) { return new HeronConfig(); }
        }

        public void Save(string path)
        {
            var sb = new StringBuilder();
            sb.Append("{\n");
            sb.Append("  \"write.enabled\": ").Append(Js(WriteEnabled)).Append(",\n");
            sb.Append("  \"publish.enabled\": ").Append(Js(PublishEnabled)).Append(",\n");
            sb.Append("  \"admin.enabled\": ").Append(Js(AdminEnabled)).Append(",\n");
            sb.Append("  \"write.askBeforeKeeping\": ").Append(Js(AskBeforeKeeping)).Append(",\n");
            sb.Append("  \"bridge.autoConnect\": ").Append(Js(AutoConnect)).Append(",\n");
            sb.Append("  \"ui.activityBanner\": ").Append(Js(ActivityBanner)).Append("\n}\n");
            AtomicFile.Write(path, sb.ToString());
        }

        private static string Js(bool value) => value ? "true" : "false";
    }

    internal static class AtomicFile
    {
        /// <summary>Write beside the target, then swap, so a reader never sees half a file.</summary>
        public static void Write(string path, string content)
        {
            var folder = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(folder)) Directory.CreateDirectory(folder);
            var temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            File.WriteAllText(temp, content, new UTF8Encoding(false));
            if (File.Exists(path)) File.Replace(temp, path, null);
            else File.Move(temp, path);
        }
    }
}
