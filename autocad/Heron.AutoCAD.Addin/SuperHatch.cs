using System;
using System.Collections.Generic;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.DatabaseServices.Filters;
using Autodesk.AutoCAD.Geometry;
using Heron.AutoCAD.Bridge;
using AcException = Autodesk.AutoCAD.Runtime.Exception;

namespace Heron.AutoCAD.Addin
{
    /// <summary>
    /// A block repeated as a hatch inside a closed outline (Express Tools'
    /// SUPERHATCH): paving, cladding, a tiled ceiling, a grating.
    ///
    /// Made as one object the modeller can move or erase: a new block holding
    /// the grid of tiles (TileGrid), inserted once at 0,0 and clipped to the
    /// outline the way XCLIP clips, with a spatial filter on the reference.
    /// </summary>
    internal static class SuperHatch
    {
        // Where XCLIP keeps a reference's clip: extension dictionary -> ACAD_FILTER -> SPATIAL.
        private const string FilterDictionary = "ACAD_FILTER";
        private const string SpatialFilterName = "SPATIAL";
        // ObjectARX's ACDB_INFINITE_XCLIP_DEPTH: no front or back clipping plane.
        private const double NoClipDepth = 1.0e+300;
        // Steps along a heavy polyline's segment, and along a spline: fixed.
        private const int SegmentSteps = 16;
        private const int CurveSteps = 128;
        // An arc is followed to within this share of the outline's size (2 mm in a 20 m room).
        private const double ArcTolerance = 1e-4;
        private const string NamePrefix = "SUPERHATCH-";

        public static RunResult Make(Database db, Transaction tr, RunArgs args)
        {
            var boundaryHandle = args.Text("boundary");
            var boundary = RunDrawing.Open<Curve>(tr, db, boundaryHandle, OpenMode.ForRead, "a closed outline (polyline, circle, ellipse or spline)");
            var outline = Outline(boundary, boundaryHandle);
            var elevation = boundary.StartPoint.Z;

            var blocks = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            var tileName = args.Text("block").Trim();
            if (tileName.Length == 0 || !blocks.Has(tileName))
                throw new RunRefusal("There is no block called '" + tileName + "' in this drawing. autocad_list_blocks lists them; "
                    + "autocad_insert_block brings one in from a .dwg.");
            var tileId = blocks[tileName];
            var tile = (BlockTableRecord)tr.GetObject(tileId, OpenMode.ForRead);
            if (tile.IsLayout || tile.IsFromExternalReference || tile.IsAnonymous)
                throw new RunRefusal("'" + tileName + "' is a layout, an xref or an unnamed block; a super hatch repeats an ordinary block.");

            var scale = args.Number("scale", 1.0);
            if (!(scale > 0)) throw new RunRefusal("The scale must be above zero.");
            var angle = args.Number("angle", 0.0);
            var (tileMin, tileMax) = TileExtents(tile, tr, scale);
            var spacing = args.Numbers("spacing");
            double stepX = spacing.Length >= 2 ? spacing[0] : tileMax[0] - tileMin[0];
            double stepY = spacing.Length >= 2 ? spacing[1] : tileMax[1] - tileMin[1];
            if (!(stepX > 0) || !(stepY > 0))
                throw new RunRefusal("'" + tileName + "' has no width or height to space the tiles by. Give the spacing.");

            var areaMin = new[] { double.MaxValue, double.MaxValue };
            var areaMax = new[] { double.MinValue, double.MinValue };
            foreach (var p in outline)
            {
                areaMin[0] = Math.Min(areaMin[0], p.X);
                areaMin[1] = Math.Min(areaMin[1], p.Y);
                areaMax[0] = Math.Max(areaMax[0], p.X);
                areaMax[1] = Math.Max(areaMax[1], p.Y);
            }
            var origin = args.Numbers("origin");
            var gridOrigin = origin.Length >= 2 ? new[] { origin[0], origin[1] } : new[] { areaMin[0], areaMin[1] };
            var error = TileGrid.Positions(areaMin, areaMax, gridOrigin, stepX, stepY, angle, tileMin, tileMax, out var positions);
            if (error != null) throw new RunRefusal(error);

            var name = args.Text("name").Trim();
            if (name.Length == 0) name = FreeName(blocks);
            else if (blocks.Has(name)) throw new RunRefusal("There is already a block called '" + name + "'. Give another name, or leave it out.");
            try
            {
                SymbolUtilityServices.ValidateSymbolName(name, false);
            }
            catch (AcException)
            {
                throw new RunRefusal("'" + name + "' cannot be a block name.");
            }

            // The tiles live in their own block, on layer 0 and colour ByBlock, so
            // the one reference's layer and colour are what the modeller sees.
            blocks.UpgradeOpen();
            var holder = new BlockTableRecord { Name = name, Origin = Point3d.Origin };
            var holderId = blocks.Add(holder);
            tr.AddNewlyCreatedDBObject(holder, true);
            foreach (var p in positions)
            {
                var piece = new BlockReference(new Point3d(p[0], p[1], elevation), tileId)
                {
                    ScaleFactors = new Scale3d(scale),
                    Rotation = angle,
                };
                holder.AppendEntity(piece);
                tr.AddNewlyCreatedDBObject(piece, true);
                piece.LayerId = db.LayerZero;
                piece.ColorIndex = 0;
            }

            var owner = (BlockTableRecord)tr.GetObject(boundary.OwnerId, OpenMode.ForWrite);
            var reference = new BlockReference(Point3d.Origin, holderId);
            reference.SetDatabaseDefaults(db);
            owner.AppendEntity(reference);
            tr.AddNewlyCreatedDBObject(reference, true);
            Clip(reference, outline, elevation, tr);

            return RunResult.Done(w =>
            {
                w.WriteBoolean("created", true);
                w.WriteString("handle", reference.Handle.ToString());
                w.WriteString("block", name);
                w.WriteString("tile", tileName);
                w.WriteNumber("tiles", positions.Count);
                w.WriteStartArray("spacing");
                w.WriteNumberValue(Math.Round(stepX, 9));
                w.WriteNumberValue(Math.Round(stepY, 9));
                w.WriteEndArray();
                w.WriteString("boundary", boundaryHandle);
                w.WriteNumber("outline_points", outline.Count);
                RunDrawing.Style(reference, db, tr, args, w);
            });
        }

        /// <summary>
        /// The outline as points in plan. Arcs are followed in short straight
        /// steps, as XCLIP itself stores a boundary: a clip is a polygon.
        /// </summary>
        private static List<Point2d> Outline(Curve curve, string handle)
        {
            var closed = curve.Closed;
            if (!closed)
            {
                try
                {
                    closed = curve.StartPoint.IsEqualTo(curve.EndPoint);
                }
                catch (AcException)
                {
                }
            }
            if (!closed) throw new RunRefusal("Outline " + handle + " is open. A super hatch fills a closed outline: close it first.");
            Plane plane;
            try
            {
                plane = curve.GetPlane();
            }
            catch (AcException)
            {
                throw new RunRefusal("Outline " + handle + " does not lie flat. A super hatch fills an outline drawn flat in plan.");
            }
            if (!plane.Normal.IsParallelTo(Vector3d.ZAxis))
                throw new RunRefusal("Outline " + handle + " is tilted. A super hatch fills an outline drawn flat in plan (world XY).");

            var tolerance = Size(curve) * ArcTolerance;
            var points = new List<Point2d>();
            if (curve is Polyline polyline)
            {
                var count = polyline.NumberOfVertices;
                var segments = polyline.Closed ? count : count - 1;
                for (var i = 0; i < segments; i++)
                {
                    var bulge = polyline.GetBulgeAt(i);
                    var steps = 1;
                    if (Math.Abs(bulge) >= 1e-12)
                    {
                        // A bulge is tan(sweep / 4); the chord and the sweep give the radius.
                        var sweep = 4 * Math.Atan(Math.Abs(bulge));
                        var chord = polyline.GetPoint2dAt(i).GetDistanceTo(polyline.GetPoint2dAt((i + 1) % count));
                        steps = TileGrid.ArcSteps(sweep, chord / (2 * Math.Sin(sweep / 2)), tolerance);
                    }
                    for (var k = 0; k < steps; k++) Add(points, polyline.GetPointAtParameter(i + (double)k / steps));
                }
            }
            else if (curve is Polyline2d || curve is Polyline3d)
            {
                // Whole parameters are the vertices: keep every corner.
                for (var i = (int)Math.Round(curve.StartParam); i < (int)Math.Round(curve.EndParam); i++)
                    for (var k = 0; k < SegmentSteps; k++) Add(points, curve.GetPointAtParameter(i + (double)k / SegmentSteps));
            }
            else
            {
                var steps = CurveSteps;
                if (curve is Circle circle) steps = TileGrid.ArcSteps(2 * Math.PI, circle.Radius, tolerance);
                else if (curve is Ellipse ellipse) steps = TileGrid.ArcSteps(2 * Math.PI, ellipse.MajorRadius, tolerance);
                double from = curve.StartParam, to = curve.EndParam;
                for (var k = 0; k < steps; k++) Add(points, curve.GetPointAtParameter(from + (to - from) * k / steps));
            }
            while (points.Count > 1 && points[points.Count - 1].IsEqualTo(points[0])) points.RemoveAt(points.Count - 1);
            if (points.Count < 3) throw new RunRefusal("Outline " + handle + " encloses no area.");
            return points;
        }

        /// <summary>The outline's size across, for the arc tolerance.</summary>
        private static double Size(Curve curve)
        {
            try
            {
                var box = curve.GeometricExtents;
                return box.MinPoint.DistanceTo(box.MaxPoint);
            }
            catch (AcException)
            {
                return 0;
            }
        }

        private static void Add(List<Point2d> points, Point3d p)
        {
            var flat = new Point2d(p.X, p.Y);
            if (points.Count == 0 || !points[points.Count - 1].IsEqualTo(flat)) points.Add(flat);
        }

        /// <summary>The tile's extents from its base point, at the scale asked for, unturned.</summary>
        private static (double[] min, double[] max) TileExtents(BlockTableRecord tile, Transaction tr, double scale)
        {
            Extents3d? box = null;
            foreach (ObjectId id in tile)
            {
                if (!(tr.GetObject(id, OpenMode.ForRead) is Entity entity) || entity is AttributeDefinition || !entity.Visible) continue;
                try
                {
                    var extents = entity.GeometricExtents;
                    if (box == null) box = extents;
                    else
                    {
                        var grow = box.Value;
                        grow.AddExtents(extents);
                        box = grow;
                    }
                }
                catch (AcException)
                {
                    // Some objects have no extents; they still go in the tile.
                }
            }
            if (box == null) throw new RunRefusal("Block '" + tile.Name + "' draws nothing, so it cannot be a hatch tile.");
            var origin = tile.Origin;
            return (
                new[] { (box.Value.MinPoint.X - origin.X) * scale, (box.Value.MinPoint.Y - origin.Y) * scale },
                new[] { (box.Value.MaxPoint.X - origin.X) * scale, (box.Value.MaxPoint.Y - origin.Y) * scale });
        }

        private static string FreeName(BlockTable blocks)
        {
            for (var n = 1; ; n++)
                if (!blocks.Has(NamePrefix + n)) return NamePrefix + n;
        }

        /// <summary>
        /// What XCLIP does: a spatial filter on the reference. The reference sits
        /// at 0,0 unscaled and unturned, so the outline's world points are also
        /// the block's own points.
        /// </summary>
        private static void Clip(BlockReference reference, List<Point2d> outline, double elevation, Transaction tr)
        {
            var definition = new SpatialFilterDefinition(new Point2dCollection(outline.ToArray()), Vector3d.ZAxis, elevation, NoClipDepth, -NoClipDepth, true);
            var filter = new SpatialFilter { Definition = definition };
            if (reference.ExtensionDictionary.IsNull) reference.CreateExtensionDictionary();
            var extension = (DBDictionary)tr.GetObject(reference.ExtensionDictionary, OpenMode.ForWrite);
            DBDictionary filters;
            if (extension.Contains(FilterDictionary))
                filters = (DBDictionary)tr.GetObject(extension.GetAt(FilterDictionary), OpenMode.ForWrite);
            else
            {
                filters = new DBDictionary();
                extension.SetAt(FilterDictionary, filters);
                tr.AddNewlyCreatedDBObject(filters, true);
            }
            filters.SetAt(SpatialFilterName, filter);
            tr.AddNewlyCreatedDBObject(filter, true);
        }
    }
}
