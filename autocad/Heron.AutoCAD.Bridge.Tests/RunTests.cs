using System.Text.Json;
using Heron.AutoCAD.Bridge;

namespace Heron.AutoCAD.Bridge.Tests;

/// <summary>
/// The "run" request: the plug-in doing one of its own operations (loft,
/// fillet, super hatch...), which COM has no call for. Same gate as typed
/// input: only inside this chat's running job, at a level that covers it.
/// </summary>
public class RunTests
{
    private const string Token = "tok";
    private readonly FakeHost _host = new();
    private readonly HeronConfig _config = new() { WriteEnabled = true };
    private readonly BridgeProtocol _protocol;

    public RunTests() =>
        _protocol = new BridgeProtocol(_host, () => _config, Token, new HeronHold(), () => DateTime.UtcNow);

    private JsonElement Send(object request) => JsonDocument.Parse(_protocol.Handle(JsonSerializer.Serialize(request))).RootElement;

    private void Begin(string risk, string job = "j1", string conversation = "chat-a") => Send(new
    {
        op = "begin", token = Token, conversation, job, tool = "autocad_fillet_solid_edges", risk, summary = "Fillet",
        drawing = @"C:\Project\M-201.dwg",
    });

    private JsonElement Run(string operation = "fillet_edges", string job = "j1", string conversation = "chat-a") =>
        Send(new { op = "run", token = Token, conversation, job, operation, args = new { handle = "2A", radius = 5.0 } });

    [Fact]
    public void Refused_without_a_running_job()
    {
        var reply = Run();
        Assert.False(reply.GetProperty("ok").GetBoolean());
        Assert.Equal(Texts.NoRunJob, reply.GetProperty("message").GetString());
        Assert.Empty(_host.Runs);
    }

    [Fact]
    public void A_change_operation_is_refused_inside_a_read_job()
    {
        Begin("read");
        Assert.False(Run("fillet_edges").GetProperty("ok").GetBoolean());
        Assert.Empty(_host.Runs);
    }

    [Fact]
    public void A_read_operation_runs_inside_a_read_job()
    {
        Begin("read");
        Assert.True(Run("solid_topology").GetProperty("ok").GetBoolean());
        Assert.Equal("solid_topology", Assert.Single(_host.Runs).Operation);
    }

    [Fact]
    public void Refused_for_another_chats_job()
    {
        Begin("change");
        Assert.False(Run(conversation: "chat-b").GetProperty("ok").GetBoolean());
        Assert.Empty(_host.Runs);
    }

    [Fact]
    public void Refused_after_the_job_ended()
    {
        Begin("change");
        Send(new { op = "end", token = Token, conversation = "chat-a", job = "j1", ok = true, outcome = "done", summary = "Fillet", ms = 5 });
        Assert.False(Run().GetProperty("ok").GetBoolean());
        Assert.Empty(_host.Runs);
    }

    [Fact]
    public void An_unknown_operation_never_reaches_AutoCAD()
    {
        // Even inside the highest level of job.
        _config.AdminEnabled = true;
        Begin("admin");
        Assert.True(Run("solid_topology").GetProperty("ok").GetBoolean());
        _host.Runs.Clear();
        var reply = Run("format_c_drive");
        Assert.False(reply.GetProperty("ok").GetBoolean());
        Assert.Equal(Texts.UnknownOperation("format_c_drive"), reply.GetProperty("message").GetString());
        Assert.Empty(_host.Runs);
    }

    [Fact]
    public void The_host_gets_the_operation_its_arguments_and_the_jobs_drawing()
    {
        Begin("change");
        Run();
        var request = Assert.Single(_host.Runs);
        Assert.Equal("fillet_edges", request.Operation);
        Assert.Equal("j1", request.Job);
        Assert.Equal(@"C:\Project\M-201.dwg", request.Drawing);
        using var args = JsonDocument.Parse(request.Args);
        Assert.Equal("2A", args.RootElement.GetProperty("handle").GetString());
        Assert.Equal(5.0, args.RootElement.GetProperty("radius").GetDouble());
    }

    [Fact]
    public void The_result_comes_back_as_json()
    {
        Begin("change");
        _host.RunAnswer = RunResult.Done(w =>
        {
            w.WriteString("handle", "2A");
            w.WriteNumber("edges", 4);
        });
        var reply = Run();
        Assert.True(reply.GetProperty("ok").GetBoolean());
        Assert.Equal("2A", reply.GetProperty("result").GetProperty("handle").GetString());
        Assert.Equal(4, reply.GetProperty("result").GetProperty("edges").GetInt32());
    }

    [Fact]
    public void A_failure_in_AutoCAD_comes_back_with_its_own_words()
    {
        Begin("change");
        _host.RunAnswer = RunResult.Failed("AutoCAD would not fillet these edges: the radius is too big. Nothing was changed.");
        var reply = Run();
        Assert.False(reply.GetProperty("ok").GetBoolean());
        Assert.Equal("Operation", reply.GetProperty("refusedBy").GetString());
        Assert.Equal("AutoCAD would not fillet these edges: the radius is too big. Nothing was changed.", reply.GetProperty("message").GetString());
    }

    [Fact]
    public void A_result_that_cannot_be_read_is_reported_as_unknown_not_as_nothing_done()
    {
        Begin("change");
        _host.RunAnswer = new RunResult { Ok = true, Json = "not json" };
        var reply = Run();
        Assert.False(reply.GetProperty("ok").GetBoolean());
        Assert.StartsWith("Outcome unknown", reply.GetProperty("message").GetString());
    }

    [Fact]
    public void Every_operation_has_a_level()
    {
        Assert.True(PluginOperations.TryLevel("solid_topology", out var read));
        Assert.Equal(Risk.Read, read);
        foreach (var name in new[] { "loft", "fillet_edges", "chamfer_edges", "shell", "press_pull", "thicken", "super_hatch" })
        {
            Assert.True(PluginOperations.TryLevel(name, out var level), name);
            Assert.Equal(Risk.Change, level);
        }
        Assert.False(PluginOperations.TryLevel("explode", out _));
    }
}

public class RunArgsTests
{
    [Fact]
    public void Values_are_read_with_their_fallbacks()
    {
        using var args = RunArgs.Parse("{\"handle\":\"2A\",\"radius\":5,\"ruled\":true,\"handles\":[\"1\",\"2\"],\"origin\":[1,2,3]}");
        Assert.Equal("2A", args.Text("handle"));
        Assert.Equal(5.0, args.Number("radius"));
        Assert.True(args.Flag("ruled", false));
        Assert.False(args.Flag("closed", false));
        Assert.Equal(new[] { "1", "2" }, args.Texts("handles"));
        Assert.Equal(new[] { 1.0, 2.0, 3.0 }, args.Numbers("origin"));
        Assert.Equal(2.5, args.Number("missing", 2.5));
        Assert.Empty(args.Texts("missing"));
    }

    [Fact]
    public void A_missing_number_with_no_fallback_is_a_refusal_naming_it()
    {
        using var args = RunArgs.Parse("{}");
        var refusal = Assert.Throws<RunRefusal>(() => args.Number("radius"));
        Assert.Contains("radius", refusal.Message);
    }

    [Fact]
    public void Arguments_that_are_not_an_object_are_refused()
    {
        Assert.Throws<RunRefusal>(() => RunArgs.Parse("[1,2]"));
        Assert.Throws<RunRefusal>(() => RunArgs.Parse("nope"));
    }
}

/// <summary>Picking a solid's edges and faces by word or by number, as the chat asks for them.</summary>
public class SolidPickTests
{
    private static TopologyPart Part(int i, double x0, double y0, double z0, double x1, double y1, double z1, string kind = "line") =>
        new() { Index = i, Kind = kind, Min = new[] { x0, y0, z0 }, Max = new[] { x1, y1, z1 } };

    /// <summary>A 10 x 20 x 30 box: four bottom edges, four top, four upright.</summary>
    private static List<TopologyPart> BoxEdges() => new()
    {
        Part(0, 0, 0, 0, 10, 0, 0), Part(1, 10, 0, 0, 10, 20, 0), Part(2, 0, 20, 0, 10, 20, 0), Part(3, 0, 0, 0, 0, 20, 0),
        Part(4, 0, 0, 30, 10, 0, 30), Part(5, 10, 0, 30, 10, 20, 30), Part(6, 0, 20, 30, 10, 20, 30), Part(7, 0, 0, 30, 0, 20, 30),
        Part(8, 0, 0, 0, 0, 0, 30), Part(9, 10, 0, 0, 10, 0, 30), Part(10, 10, 20, 0, 10, 20, 30), Part(11, 0, 20, 0, 0, 20, 30),
    };

    private static List<TopologyPart> BoxFaces() => new()
    {
        Part(0, 0, 0, 0, 10, 20, 0, "plane"), Part(1, 0, 0, 30, 10, 20, 30, "plane"),
        Part(2, 0, 0, 0, 10, 0, 30, "plane"), Part(3, 0, 20, 0, 10, 20, 30, "plane"),
        Part(4, 0, 0, 0, 0, 20, 30, "plane"), Part(5, 10, 0, 0, 10, 20, 30, "plane"),
    };

    private static JsonElement J(string json) => JsonDocument.Parse(json).RootElement;

    private static int[] Pick(List<TopologyPart> parts, string json, PartKind kind)
    {
        var error = SolidPicks.Choose(parts, J(json), kind, out var picked);
        Assert.Null(error);
        return picked;
    }

    [Theory]
    [InlineData("\"all\"", new[] { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 })]
    [InlineData("\"vertical\"", new[] { 8, 9, 10, 11 })]
    [InlineData("\"horizontal\"", new[] { 0, 1, 2, 3, 4, 5, 6, 7 })]
    [InlineData("\"top\"", new[] { 4, 5, 6, 7 })]
    [InlineData("\"bottom\"", new[] { 0, 1, 2, 3 })]
    [InlineData("\"TOP\"", new[] { 4, 5, 6, 7 })]
    public void Edge_words(string json, int[] expected) => Assert.Equal(expected, Pick(BoxEdges(), json, PartKind.Edge));

    [Theory]
    [InlineData("\"top\"", 1)]
    [InlineData("\"bottom\"", 0)]
    [InlineData("\"front\"", 2)]
    [InlineData("\"back\"", 3)]
    [InlineData("\"left\"", 4)]
    [InlineData("\"right\"", 5)]
    public void Face_words_follow_AutoCADs_view_names(string json, int expected) =>
        Assert.Equal(new[] { expected }, Pick(BoxFaces(), json, PartKind.Face));

    [Fact]
    public void Numbers_are_taken_as_given_once_each() => Assert.Equal(new[] { 3, 0 }, Pick(BoxEdges(), "[3, 0, 3]", PartKind.Edge));

    [Fact]
    public void A_number_that_is_not_there_is_named_with_the_range()
    {
        var error = SolidPicks.Choose(BoxEdges(), J("[12]"), PartKind.Edge, out _);
        Assert.NotNull(error);
        Assert.Contains("12", error);
        Assert.Contains("0-11", error);
    }

    [Fact]
    public void An_unknown_word_lists_the_ones_there_are()
    {
        var error = SolidPicks.Choose(BoxEdges(), J("\"diagonal\""), PartKind.Edge, out _);
        Assert.NotNull(error);
        Assert.Contains("vertical", error);
    }

    [Fact]
    public void A_face_word_is_not_an_edge_word()
    {
        Assert.NotNull(SolidPicks.Choose(BoxEdges(), J("\"front\""), PartKind.Edge, out _));
        Assert.NotNull(SolidPicks.Choose(BoxFaces(), J("\"vertical\""), PartKind.Face, out _));
    }

    [Fact]
    public void A_word_that_picks_nothing_says_so()
    {
        // A cylinder: a circle at the bottom, one at the top, nothing upright and straight.
        var cylinder = new List<TopologyPart> { Part(0, -5, -5, 0, 5, 5, 0, "circle"), Part(1, -5, -5, 30, 5, 5, 30, "circle") };
        var error = SolidPicks.Choose(cylinder, J("\"vertical\""), PartKind.Edge, out _);
        Assert.NotNull(error);
        Assert.Contains("No edge", error);
        Assert.Equal(new[] { 1 }, Pick(cylinder, "\"top\"", PartKind.Edge));
    }

    [Fact]
    public void Nothing_to_pick_from_is_said_plainly()
    {
        // A sphere has one face and no edges.
        var error = SolidPicks.Choose(new List<TopologyPart>(), J("\"all\""), PartKind.Edge, out _);
        Assert.NotNull(error);
        Assert.Contains("no edges", error);
    }

    [Fact]
    public void An_empty_list_is_refused() => Assert.NotNull(SolidPicks.Choose(BoxEdges(), J("[]"), PartKind.Edge, out _));

    [Fact]
    public void Rounding_noise_does_not_lose_the_top_face()
    {
        var faces = BoxFaces();
        faces[1] = Part(1, 0, 0, 30.0000000001, 10, 20, 29.9999999999, "plane");
        Assert.Equal(new[] { 1 }, Pick(faces, "\"top\"", PartKind.Face));
    }
}

/// <summary>Where the tiles of a super hatch go: enough to cover the area, no more.</summary>
public class TileGridTests
{
    private static List<double[]> Grid(double[] areaMin, double[] areaMax, double[] origin, double step, double angle, double[] tileMin, double[] tileMax)
    {
        var error = TileGrid.Positions(areaMin, areaMax, origin, step, step, angle, tileMin, tileMax, out var positions);
        Assert.Null(error);
        return positions;
    }

    private static string Text(List<double[]> positions) =>
        string.Join(" ", positions.Select(p => "(" + Math.Round(p[0], 6) + "," + Math.Round(p[1], 6) + ")").OrderBy(s => s, StringComparer.Ordinal));

    [Fact]
    public void Square_tiles_from_the_corner_cover_the_area_exactly()
    {
        var positions = Grid(new[] { 0.0, 0.0 }, new[] { 10.0, 10.0 }, new[] { 0.0, 0.0 }, 5, 0, new[] { 0.0, 0.0 }, new[] { 5.0, 5.0 });
        Assert.Equal("(0,0) (0,5) (5,0) (5,5)", Text(positions));
    }

    [Fact]
    public void An_origin_inside_the_area_still_covers_all_of_it()
    {
        var positions = Grid(new[] { 0.0, 0.0 }, new[] { 10.0, 10.0 }, new[] { 2.0, 2.0 }, 5, 0, new[] { 0.0, 0.0 }, new[] { 5.0, 5.0 });
        Assert.Equal(9, positions.Count);
        Assert.Contains(positions, p => Math.Abs(p[0] + 3) < 1e-9 && Math.Abs(p[1] + 3) < 1e-9);
    }

    [Fact]
    public void A_tile_drawn_round_its_base_point_is_allowed_for()
    {
        var positions = Grid(new[] { 0.0, 0.0 }, new[] { 10.0, 10.0 }, new[] { 0.0, 0.0 }, 5, 0, new[] { -2.5, -2.5 }, new[] { 2.5, 2.5 });
        Assert.Equal(9, positions.Count);
    }

    [Fact]
    public void A_turned_grid_still_covers_every_corner()
    {
        double[] min = { 0, 0 }, max = { 12, 7 };
        var angle = Math.PI / 6;
        var positions = Grid(min, max, new[] { 1.0, 1.0 }, 3, angle, new[] { 0.0, 0.0 }, new[] { 3.0, 3.0 });
        foreach (var corner in new[] { new[] { 0.0, 0.0 }, new[] { 12.0, 0.0 }, new[] { 12.0, 7.0 }, new[] { 0.0, 7.0 }, new[] { 6.0, 3.5 } })
        {
            var covered = positions.Any(p =>
            {
                double dx = corner[0] - p[0], dy = corner[1] - p[1];
                double u = dx * Math.Cos(angle) + dy * Math.Sin(angle), v = -dx * Math.Sin(angle) + dy * Math.Cos(angle);
                return u >= -1e-9 && u <= 3 + 1e-9 && v >= -1e-9 && v <= 3 + 1e-9;
            });
            Assert.True(covered, "corner " + corner[0] + "," + corner[1]);
        }
    }

    [Fact]
    public void Too_many_tiles_is_refused_before_any_is_made()
    {
        var error = TileGrid.Positions(new[] { 0.0, 0.0 }, new[] { 10000.0, 10000.0 }, new[] { 0.0, 0.0 }, 1, 1, 0,
            new[] { 0.0, 0.0 }, new[] { 1.0, 1.0 }, out var positions);
        Assert.NotNull(error);
        Assert.Contains(TileGrid.MostTiles.ToString(), error);
        Assert.Empty(positions);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-2.0)]
    public void A_spacing_that_is_not_above_zero_is_refused(double step)
    {
        Assert.NotNull(TileGrid.Positions(new[] { 0.0, 0.0 }, new[] { 10.0, 10.0 }, new[] { 0.0, 0.0 }, step, 5, 0,
            new[] { 0.0, 0.0 }, new[] { 5.0, 5.0 }, out _));
    }
}

/// <summary>An operation only runs on the drawing its job began on.</summary>
public class DrawingNameTests
{
    [Theory]
    [InlineData(@"C:\Project\M-201.dwg", @"C:\Project\M-201.dwg")]
    [InlineData(@"C:\Project\M-201.dwg", @"c:\project\m-201.DWG")]
    [InlineData("Drawing1.dwg", "Drawing1.dwg")]
    [InlineData(@"C:\Users\aj\Documents\Drawing1.dwg", "Drawing1.dwg")]
    [InlineData(@"C:\Project\M-201.dwg", "")]
    public void The_same_drawing(string active, string job) => Assert.True(DrawingNames.Same(active, job));

    [Theory]
    [InlineData(@"C:\Project\M-201.dwg", @"C:\Project\M-202.dwg")]
    [InlineData(@"C:\Project\M-201.dwg", @"D:\Old\M-201.dwg")]
    [InlineData("Drawing2.dwg", "Drawing1.dwg")]
    public void Another_drawing(string active, string job) => Assert.False(DrawingNames.Same(active, job));
}
