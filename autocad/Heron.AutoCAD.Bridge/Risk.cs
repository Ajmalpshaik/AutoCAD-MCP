namespace Heron.AutoCAD.Bridge
{
    /// <summary>What a tool may do. The Python server declares it per tool (core/risk.py).</summary>
    public enum Risk { Read, View, Change, Publish, Admin }

    public static class RiskNames
    {
        public static bool TryParse(string? text, out Risk risk)
        {
            switch (text)
            {
                case "read": risk = Risk.Read; return true;
                case "view": risk = Risk.View; return true;
                case "change": risk = Risk.Change; return true;
                case "publish": risk = Risk.Publish; return true;
                case "admin": risk = Risk.Admin; return true;
                default: risk = Risk.Admin; return false;
            }
        }
    }
}
