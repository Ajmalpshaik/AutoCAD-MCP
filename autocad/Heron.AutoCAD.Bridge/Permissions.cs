namespace Heron.AutoCAD.Bridge
{
    public sealed class Refusal
    {
        public Refusal(string refusedBy, string message)
        {
            RefusedBy = refusedBy;
            Message = message;
        }

        public string RefusedBy { get; }
        public string Message { get; }
    }

    /// <summary>
    /// Which padlock a level needs. Changes comes first for everything that
    /// writes: Publish and Admin only widen what Changes already allows.
    /// </summary>
    public static class Permissions
    {
        public static Refusal? Refusal(Risk risk, HeronConfig config)
        {
            if (risk == Risk.Read || risk == Risk.View) return null;
            if (!config.WriteEnabled) return new Refusal("Changes", Texts.ChangesOff);
            if (risk == Risk.Publish && !config.PublishEnabled) return new Refusal("Publish", Texts.PublishOff);
            if (risk == Risk.Admin && !config.AdminEnabled) return new Refusal("Admin", Texts.AdminOff);
            return null;
        }
    }
}
