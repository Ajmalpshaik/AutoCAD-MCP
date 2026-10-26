using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace Heron.AutoCAD.Addin
{
    /// <summary>The few look-and-feel pieces the Heron windows share.</summary>
    internal static class HeronUi
    {
        public static readonly Brush Ink = new SolidColorBrush(Color.FromRgb(0x1F, 0x23, 0x28));
        public static readonly Brush Muted = new SolidColorBrush(Color.FromRgb(0x5B, 0x64, 0x6E));
        public static readonly Brush Amber = new SolidColorBrush(Color.FromRgb(0xF0, 0xA3, 0x2C));
        public static readonly Brush Grey = new SolidColorBrush(Color.FromRgb(0xB8, 0xBF, 0xC6));
        public static readonly Brush Line = new SolidColorBrush(Color.FromRgb(0xE1, 0xE4, 0xE8));

        public static Window NewWindow(string title, double width) => new Window
        {
            Title = title,
            Width = width,
            SizeToContent = SizeToContent.Height,
            ResizeMode = ResizeMode.NoResize,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            ShowInTaskbar = false,
            FontFamily = new FontFamily("Segoe UI"),
            Background = Brushes.White,
        };

        public static TextBlock Text(string text, double size = 13, FontWeight? weight = null, Brush? color = null) => new TextBlock
        {
            Text = text,
            FontSize = size,
            FontWeight = weight ?? FontWeights.Normal,
            Foreground = color ?? Ink,
            TextWrapping = TextWrapping.Wrap,
            Margin = new Thickness(0, 0, 0, 6),
        };

        public static Button Button(string text, bool isDefault = false, bool isCancel = false) => new Button
        {
            Content = text,
            MinWidth = 96,
            Padding = new Thickness(14, 5, 14, 5),
            Margin = new Thickness(8, 0, 0, 0),
            IsDefault = isDefault,
            IsCancel = isCancel,
        };

        /// <summary>A switch card: amber ON, grey OFF, never green (green would read as "safe").</summary>
        public static Border Card(string name, bool on, string onText, string offText)
        {
            var chip = new Border
            {
                Background = on ? Amber : Grey,
                CornerRadius = new CornerRadius(3),
                Padding = new Thickness(6, 1, 6, 1),
                Margin = new Thickness(0, 0, 10, 0),
                VerticalAlignment = VerticalAlignment.Top,
                Child = new TextBlock { Text = on ? "ON" : "OFF", FontSize = 11, FontWeight = FontWeights.Bold, Foreground = Brushes.White },
            };
            var words = new StackPanel();
            words.Children.Add(Text(name, 13, FontWeights.SemiBold));
            var detail = Text(on ? onText : offText, 12, null, Muted);
            detail.Margin = new Thickness(0);
            words.Children.Add(detail);
            var row = new DockPanel();
            DockPanel.SetDock(chip, Dock.Left);
            row.Children.Add(chip);
            row.Children.Add(words);
            return new Border
            {
                BorderBrush = Line,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(6),
                Padding = new Thickness(10, 8, 10, 8),
                Margin = new Thickness(0, 0, 0, 6),
                Child = row,
            };
        }

        public static StackPanel Buttons(params Button[] buttons)
        {
            var panel = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0) };
            foreach (var b in buttons) panel.Children.Add(b);
            return panel;
        }
    }
}
