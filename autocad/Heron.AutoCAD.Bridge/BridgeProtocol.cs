using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;

namespace Heron.AutoCAD.Bridge
{
    /// <summary>
    /// One request line in, one reply line out. No pipes and no AutoCAD here,
    /// so every rule the bridge enforces is tested offline.
    ///
    /// Ops: ping, info, release, begin, end, ask_keep. Every op needs the
    /// session token. begin is where the hold and the padlocks are checked.
    /// </summary>
    public sealed class BridgeProtocol
    {
        public const int Version = 1;
        public static readonly TimeSpan KeepGrantIdle = TimeSpan.FromMinutes(10);

        private readonly IJobHost _host;
        private readonly Func<HeronConfig> _config;
        private readonly string _token;
        private readonly HeronHold _hold;
        private readonly Func<DateTime> _clock;
        private readonly object _grantGate = new object();
        private string? _grantConversation;
        private DateTime _grantLast;

        public BridgeProtocol(IJobHost host, Func<HeronConfig> config, string token, HeronHold hold, Func<DateTime> clock)
        {
            _host = host;
            _config = config;
            _token = token;
            _hold = hold;
            _clock = clock;
        }

        /// <summary>Set by the server so info can report it.</summary>
        public Dictionary<string, object> Info { get; } = new Dictionary<string, object>();

        /// <summary>True while a "keep the rest of this job" grant stands (the ribbon shows it).</summary>
        public bool KeepGrantActive
        {
            get
            {
                lock (_grantGate) return _grantConversation != null && _clock() - _grantLast < KeepGrantIdle;
            }
        }

        public void ClearKeepGrant()
        {
            lock (_grantGate) _grantConversation = null;
        }

        public string Handle(string line)
        {
            JsonDocument doc;
            try
            {
                doc = JsonDocument.Parse(line);
            }
            catch (JsonException)
            {
                return Refuse("BadRequest", Texts.BadRequest);
            }

            using (doc)
            {
                var root = doc.RootElement;
                if (root.ValueKind != JsonValueKind.Object) return Refuse("BadRequest", Texts.BadRequest);
                var op = Str(root, "op");
                if (!BridgeIdentity.TokenEquals(_token, Str(root, "token"))) return Refuse("Session", Texts.WrongSession);
                var conversation = Str(root, "conversation");

                try
                {
                    switch (op)
                    {
                        case "ping":
                            return Ok(w => w.WriteNumber("protocolVersion", Version));
                        case "info":
                            return Ok(w =>
                            {
                                w.WriteNumber("protocolVersion", Version);
                                foreach (var pair in Info) w.WriteString(pair.Key, pair.Value?.ToString());
                            });
                        case "release":
                            _hold.Release(conversation);
                            return Ok(null);
                        case "begin":
                            return Begin(root, conversation);
                        case "end":
                            return End(root, conversation);
                        case "ask_keep":
                            return AskKeep(root, conversation);
                        default:
                            return Refuse("BadRequest", Texts.UnknownOp(op));
                    }
                }
                catch (Exception ex)
                {
                    return Refuse("Error", "Heron in AutoCAD hit an error: " + ex.Message + " " + Texts.NothingSent);
                }
            }
        }

        private string Begin(JsonElement root, string conversation)
        {
            if (!RiskNames.TryParse(Str(root, "risk"), out var risk)) return Refuse("Level", Texts.UnknownRisk);
            if (!_hold.TryTake(conversation, _clock())) return Refuse("InUse", Texts.InUse);
            var config = _config();
            var refusal = Permissions.Refusal(risk, config);
            if (refusal != null) return Refuse(refusal.RefusedBy, refusal.Message);

            // Told up front, so the server puts an UNDO mark down only for a
            // job that will be asked about, and asks only then.
            bool askToKeep;
            lock (_grantGate)
            {
                var granted = _grantConversation == conversation && _clock() - _grantLast < KeepGrantIdle;
                askToKeep = config.AskBeforeKeeping && !granted;
            }

            var job = new JobInfo
            {
                Job = Str(root, "job"),
                Tool = Str(root, "tool"),
                Risk = risk,
                Summary = Str(root, "summary"),
                Drawing = Str(root, "drawing"),
                Conversation = conversation,
            };
            try
            {
                _host.Begin(job);
            }
            catch (Exception)
            {
                // The banner is something to see, not a gate: a drawing glitch
                // must not stop a job the padlocks allowed.
            }
            return Ok(w => w.WriteBoolean("askToKeep", askToKeep));
        }

        private string End(JsonElement root, string conversation)
        {
            _hold.TryTake(conversation, _clock());
            var end = new JobEnd
            {
                Job = Str(root, "job"),
                Ok = root.TryGetProperty("ok", out var ok) && ok.ValueKind == JsonValueKind.True,
                Outcome = Str(root, "outcome"),
                Summary = Str(root, "summary"),
                Ms = root.TryGetProperty("ms", out var ms) && ms.ValueKind == JsonValueKind.Number ? ms.GetInt32() : 0,
            };
            try
            {
                _host.End(end);
            }
            catch (Exception)
            {
            }
            return Ok(null);
        }

        private string AskKeep(JsonElement root, string conversation)
        {
            if (!_config().AskBeforeKeeping) return Answer("keep");
            lock (_grantGate)
            {
                if (_grantConversation == conversation && _clock() - _grantLast < KeepGrantIdle)
                {
                    _grantLast = _clock();
                    return Answer("keep");
                }
                _grantConversation = null;
            }

            var handles = new List<string>();
            if (root.TryGetProperty("handles", out var list) && list.ValueKind == JsonValueKind.Array)
                foreach (var item in list.EnumerateArray())
                    if (item.ValueKind == JsonValueKind.String) handles.Add(item.GetString() ?? "");

            string answer;
            try
            {
                answer = _host.AskKeep(new KeepRequest { Job = Str(root, "job"), Summary = Str(root, "summary"), Handles = handles.ToArray() });
            }
            catch (Exception)
            {
                answer = "discard";
            }
            if (answer != "keep" && answer != "keep_rest") answer = "discard";
            if (answer == "keep_rest")
                lock (_grantGate)
                {
                    _grantConversation = conversation;
                    _grantLast = _clock();
                }
            return Answer(answer);
        }

        private static string Str(JsonElement root, string name) =>
            root.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() ?? "" : "";

        private static string Answer(string answer) => Ok(w => w.WriteString("answer", answer));

        private static string Refuse(string refusedBy, string message) => Write(w =>
        {
            w.WriteBoolean("ok", false);
            w.WriteString("refusedBy", refusedBy);
            w.WriteString("message", message);
        });

        private static string Ok(Action<Utf8JsonWriter>? more) => Write(w =>
        {
            w.WriteBoolean("ok", true);
            more?.Invoke(w);
        });

        private static string Write(Action<Utf8JsonWriter> body)
        {
            using (var stream = new MemoryStream())
            {
                using (var writer = new Utf8JsonWriter(stream))
                {
                    writer.WriteStartObject();
                    body(writer);
                    writer.WriteEndObject();
                }
                return Encoding.UTF8.GetString(stream.ToArray());
            }
        }
    }
}
