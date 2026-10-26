using System;
using System.Security.Cryptography;
using System.Text;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>The per-connect session token: minted on every connect, gone on disconnect.</summary>
    public static class BridgeIdentity
    {
        public static string MintToken()
        {
            var bytes = new byte[24];
            using (var rng = RandomNumberGenerator.Create()) rng.GetBytes(bytes);
            return Convert.ToBase64String(bytes);
        }

        /// <summary>Constant-time compare, so a wrong token gives nothing away by timing.</summary>
        public static bool TokenEquals(string? expected, string? given)
        {
            if (expected == null || given == null) return false;
            var a = Encoding.UTF8.GetBytes(expected);
            var b = Encoding.UTF8.GetBytes(given);
            var diff = a.Length ^ b.Length;
            for (var i = 0; i < Math.Min(a.Length, b.Length); i++) diff |= a[i] ^ b[i];
            return diff == 0;
        }
    }
}
