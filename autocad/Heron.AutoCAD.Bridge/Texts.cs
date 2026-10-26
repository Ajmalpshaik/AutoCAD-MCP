namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// Every sentence the bridge says to a chat. Kept in one place so the
    /// Python side, the docs and the tests quote the same words.
    /// </summary>
    public static class Texts
    {
        public const string NothingSent = "Nothing was sent to AutoCAD.";

        public const string WrongSession =
            "This chat holds an old or wrong Heron session for this AutoCAD. Press Heron in AutoCAD to connect again. " + NothingSent;

        public const string InUse = "This AutoCAD is in use by another chat. " + NothingSent;

        public const string ChangesOff =
            "Changes is off, so Heron may not change this drawing. To allow it, click the Changes padlock on the Heron tab in AutoCAD (or type HERONCHANGES). " + NothingSent;

        public const string PublishOff =
            "Publish is off, so Heron may not save, export or plot drawings. To allow it, click the Publish padlock on the Heron tab in AutoCAD (or type HERONPUBLISH). " + NothingSent;

        public const string AdminOff =
            "Admin is off, so Heron may not run AutoCAD commands, AutoLISP or system-variable changes. To allow it, click the Admin padlock on the Heron tab in AutoCAD (or type HERONADMIN). " + NothingSent;

        public const string UnknownRisk =
            "Heron in AutoCAD did not recognise this tool's level, so it refused it. " + NothingSent;

        public const string BadRequest = "Heron in AutoCAD could not read the request. " + NothingSent;

        public static string UnknownOp(string op) =>
            "Heron in AutoCAD does not know the request '" + op + "'. Update Heron so both sides match. " + NothingSent;
    }
}
