namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// What the add-in does for a job: the banner, the command-line line and
    /// the Keep or Discard box. The bridge decides; the host only shows.
    /// </summary>
    public interface IJobHost
    {
        void Begin(JobInfo job);
        void End(JobEnd end);

        /// <summary>keep | discard | keep_rest. Called on a pipe thread; may wait for the modeller.</summary>
        string AskKeep(KeepRequest request);
    }

    public sealed class JobInfo
    {
        public string Job { get; set; } = "";
        public string Tool { get; set; } = "";
        public Risk Risk { get; set; }
        public string Summary { get; set; } = "";
        public string Drawing { get; set; } = "";
        public string Conversation { get; set; } = "";
    }

    public sealed class JobEnd
    {
        public string Job { get; set; } = "";
        public bool Ok { get; set; }
        public string Outcome { get; set; } = "";
        public string Summary { get; set; } = "";
        public int Ms { get; set; }
    }

    public sealed class KeepRequest
    {
        public string Job { get; set; } = "";
        public string Summary { get; set; } = "";
        public string[] Handles { get; set; } = new string[0];
    }
}
