using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Heron.AutoCAD.Bridge
{
    public enum PartKind { Edge, Face }

    /// <summary>
    /// One edge or face of a solid, as far as picking needs it: its number
    /// (its place in the list) and the world box round it.
    /// </summary>
    public sealed class TopologyPart
    {
        public int Index { get; set; }
        public string Kind { get; set; } = "";
        public double[] Min { get; set; } = new double[3];
        public double[] Max { get; set; } = new double[3];
    }

    /// <summary>
    /// Which edges or faces the chat means: a word ("top", "vertical"...) or
    /// numbers from the listing. Pure, so every rule is tested offline.
    ///
    /// The words go by the solid's world box, never by a face's normal: a flat
    /// face on the top of the box can only face up, whatever way the modelling
    /// kernel stored it. Face words follow AutoCAD's view names (the front is
    /// what the Front view looks at, the side towards -Y).
    /// </summary>
    public static class SolidPicks
    {
        public static readonly string[] EdgeWords = { "all", "vertical", "horizontal", "top", "bottom" };
        public static readonly string[] FaceWords = { "top", "bottom", "front", "back", "left", "right" };

        private const string Lister = "autocad_list_solid_faces_and_edges";

        /// <summary>Null and the numbers picked, or why nothing could be picked.</summary>
        public static string? Choose(IList<TopologyPart> parts, JsonElement selector, PartKind kind, out int[] picked)
        {
            picked = new int[0];
            var noun = kind == PartKind.Edge ? "edge" : "face";
            var words = kind == PartKind.Edge ? EdgeWords : FaceWords;
            if (parts.Count == 0) return "This solid has no " + noun + "s to pick (a sphere has one face and no edges).";

            if (selector.ValueKind == JsonValueKind.Array)
            {
                var list = new List<int>();
                foreach (var item in selector.EnumerateArray())
                {
                    if (item.ValueKind != JsonValueKind.Number || !item.TryGetInt32(out var number))
                        return "Give the " + noun + "s as whole numbers from " + Lister + ".";
                    if (number < 0 || number >= parts.Count)
                        return "There is no " + noun + " " + number + ": this solid has " + parts.Count + " " + noun + "s, numbered 0-"
                            + (parts.Count - 1) + ". " + Lister + " lists them.";
                    if (!list.Contains(number)) list.Add(number);
                }
                if (list.Count == 0) return "Name at least one " + noun + ".";
                picked = list.ToArray();
                return null;
            }

            if (selector.ValueKind != JsonValueKind.String)
                return "Name the " + noun + "s with a word (" + string.Join(", ", words) + ") or a list of numbers.";
            var word = (selector.GetString() ?? "").Trim().ToLowerInvariant();
            if (Array.IndexOf(words, word) < 0)
                return "'" + word + "' is not a way to pick " + noun + "s. Use one of: " + string.Join(", ", words) + ", or a list of numbers from " + Lister + ".";

            var low = new[] { double.MaxValue, double.MaxValue, double.MaxValue };
            var high = new[] { double.MinValue, double.MinValue, double.MinValue };
            foreach (var part in parts)
                for (var axis = 0; axis < 3; axis++)
                {
                    low[axis] = Math.Min(low[axis], Math.Min(part.Min[axis], part.Max[axis]));
                    high[axis] = Math.Max(high[axis], Math.Max(part.Min[axis], part.Max[axis]));
                }
            var tolerance = Tolerance(low, high);

            var chosen = new List<int>();
            for (var i = 0; i < parts.Count; i++)
                if (Matches(parts[i], word, kind, low, high, tolerance)) chosen.Add(i);
            if (chosen.Count == 0)
                return "No " + noun + " of this solid is '" + word + "'. " + Lister + " lists them, with numbers to pick from.";
            picked = chosen.ToArray();
            return null;
        }

        /// <summary>A millionth of the solid's size: flat is flat to the modeller, not to the last digit.</summary>
        public static double Tolerance(double[] low, double[] high)
        {
            double dx = high[0] - low[0], dy = high[1] - low[1], dz = high[2] - low[2];
            return Math.Max(1e-9, Math.Sqrt(dx * dx + dy * dy + dz * dz) * 1e-6);
        }

        private static bool Matches(TopologyPart part, string word, PartKind kind, double[] low, double[] high, double tolerance)
        {
            double Size(int axis) => Math.Abs(part.Max[axis] - part.Min[axis]);
            bool At(int axis, double[] side) => Math.Abs(part.Min[axis] - side[axis]) <= tolerance && Math.Abs(part.Max[axis] - side[axis]) <= tolerance;
            bool Flat(int axis) => Size(axis) <= tolerance;

            if (kind == PartKind.Edge)
            {
                switch (word)
                {
                    case "all": return true;
                    case "vertical": return Flat(0) && Flat(1) && !Flat(2);
                    case "horizontal": return Flat(2);
                    case "top": return Flat(2) && At(2, high);
                    case "bottom": return Flat(2) && At(2, low);
                    default: return false;
                }
            }
            switch (word)
            {
                case "top": return Flat(2) && At(2, high);
                case "bottom": return Flat(2) && At(2, low);
                case "front": return Flat(1) && At(1, low);
                case "back": return Flat(1) && At(1, high);
                case "left": return Flat(0) && At(0, low);
                case "right": return Flat(0) && At(0, high);
                default: return false;
            }
        }
    }
}
