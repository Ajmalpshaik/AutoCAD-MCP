using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// Something the chat asked for that cannot be done, in words for the chat.
    /// The plug-in throws it inside an operation; nothing it began is kept.
    /// </summary>
    public sealed class RunRefusal : Exception
    {
        public RunRefusal(string message) : base(message) { }
    }

    /// <summary>An operation's arguments, read with plain fallbacks.</summary>
    public sealed class RunArgs : IDisposable
    {
        private readonly JsonDocument _doc;

        private RunArgs(JsonDocument doc) => _doc = doc;

        public static RunArgs Parse(string json)
        {
            JsonDocument doc;
            try
            {
                doc = JsonDocument.Parse(string.IsNullOrWhiteSpace(json) ? "{}" : json);
            }
            catch (JsonException)
            {
                throw new RunRefusal("Heron in AutoCAD could not read the operation's arguments.");
            }
            if (doc.RootElement.ValueKind != JsonValueKind.Object)
            {
                doc.Dispose();
                throw new RunRefusal("Heron in AutoCAD could not read the operation's arguments.");
            }
            return new RunArgs(doc);
        }

        public JsonElement Root => _doc.RootElement;

        public bool Has(string name) =>
            Root.TryGetProperty(name, out var value) && value.ValueKind != JsonValueKind.Null;

        public string Text(string name, string fallback = "") =>
            Root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() ?? fallback : fallback;

        /// <summary>A number; without a fallback a missing one is a refusal that names it.</summary>
        public double Number(string name, double? fallback = null)
        {
            if (Root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Number) return value.GetDouble();
            if (fallback.HasValue) return fallback.Value;
            throw new RunRefusal("The operation needs '" + name + "' as a number.");
        }

        public bool Flag(string name, bool fallback)
        {
            if (!Root.TryGetProperty(name, out var value)) return fallback;
            if (value.ValueKind == JsonValueKind.True) return true;
            if (value.ValueKind == JsonValueKind.False) return false;
            return fallback;
        }

        public string[] Texts(string name)
        {
            var list = new List<string>();
            if (Root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Array)
                foreach (var item in value.EnumerateArray())
                    if (item.ValueKind == JsonValueKind.String) list.Add(item.GetString() ?? "");
            return list.ToArray();
        }

        public double[] Numbers(string name)
        {
            var list = new List<double>();
            if (Root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Array)
                foreach (var item in value.EnumerateArray())
                    if (item.ValueKind == JsonValueKind.Number) list.Add(item.GetDouble());
            return list.ToArray();
        }

        /// <summary>The raw value, or an undefined element when it is not there.</summary>
        public JsonElement Element(string name) => Root.TryGetProperty(name, out var value) ? value : default;

        public void Dispose() => _doc.Dispose();
    }
}
