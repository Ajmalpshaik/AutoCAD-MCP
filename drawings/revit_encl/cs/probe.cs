var title = doc.Title;
var isFamily = doc.IsFamilyDocument;
var version = app.VersionNumber + " / " + app.VersionBuild;
var templates = app.FamilyTemplatePath;
var path = doc.PathName;
var units = doc.GetUnits().GetFormatOptions(UnitType.UT_Length).DisplayUnits.ToString();
var titleblocks = new FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType().GetElementCount();
var levels = string.Join(", ", new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().Select(l => l.Name + "@" + Math.Round(l.Elevation * 304.8)));
