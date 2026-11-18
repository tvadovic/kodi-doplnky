# Vygeneruje icon.png (512x512) a fanart.jpg (1920x1080) doplnku.
# Vlastná grafika (retro televízor + play), nepoužíva logo STVR.
# Spustenie: powershell -ExecutionPolicy Bypass -File dev\make_art.ps1

Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot

function New-RoundRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = 2 * $r
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}

$navyDark = [System.Drawing.Color]::FromArgb(255, 9, 24, 48)
$navy = [System.Drawing.Color]::FromArgb(255, 25, 72, 135)
$coral = [System.Drawing.Color]::FromArgb(255, 255, 107, 74)
$white = [System.Drawing.Color]::White

# Nakreslí televízor s play tlačidlom; (cx, top) = stred hore, s = mierka (šírka TV)
function Draw-TV($g, [float]$cx, [float]$top, [float]$s, [int]$alpha) {
    $line = [System.Drawing.Color]::FromArgb($alpha, 255, 255, 255)
    $fill = [System.Drawing.Color]::FromArgb([int]($alpha * 0.10), 255, 255, 255)
    $play = [System.Drawing.Color]::FromArgb($alpha, $coral.R, $coral.G, $coral.B)
    $pen = New-Object System.Drawing.Pen($line, [float]($s * 0.05))
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $w = $s; $h = $s * 0.66
    $x = $cx - $w / 2; $y = $top + $s * 0.22
    # anténa
    $g.DrawLine($pen, $cx, $y - $s * 0.02, $cx - $s * 0.18, $top)
    $g.DrawLine($pen, $cx, $y - $s * 0.02, $cx + $s * 0.18, $top)
    # telo a obrazovka
    $body = New-RoundRect $x $y $w $h ($s * 0.11)
    $g.FillPath((New-Object System.Drawing.SolidBrush($fill)), $body)
    $g.DrawPath($pen, $body)
    # nožičky
    $g.DrawLine($pen, $x + $w * 0.22, $y + $h + $s * 0.02, $x + $w * 0.17, $y + $h + $s * 0.09)
    $g.DrawLine($pen, $x + $w * 0.78, $y + $h + $s * 0.02, $x + $w * 0.83, $y + $h + $s * 0.09)
    # play
    $pcx = $cx + $s * 0.03; $pcy = $y + $h / 2; $r = $s * 0.19
    $pts = @(
        (New-Object System.Drawing.PointF(($pcx - $r * 0.8), ($pcy - $r))),
        (New-Object System.Drawing.PointF(($pcx + $r), $pcy)),
        (New-Object System.Drawing.PointF(($pcx - $r * 0.8), ($pcy + $r)))
    )
    $tri = New-Object System.Drawing.Drawing2D.GraphicsPath
    $tri.AddPolygon($pts)
    $g.FillPath((New-Object System.Drawing.SolidBrush($play)), $tri)
    $ppen = New-Object System.Drawing.Pen($play, [float]($s * 0.04))
    $ppen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $g.DrawPath($ppen, $tri)
}

function Set-Quality($g) {
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
}

# ---------------- icon.png
$size = 512
$bmp = New-Object System.Drawing.Bitmap($size, $size)
$g = [System.Drawing.Graphics]::FromImage($bmp)
Set-Quality $g
$g.Clear([System.Drawing.Color]::Transparent)
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Point(0, 0)), (New-Object System.Drawing.Point($size, $size)), $navy, $navyDark)
$g.FillPath($bg, (New-RoundRect 0 0 $size $size 96))
Draw-TV $g 256 70 300 255

$text = "ARCH" + [char]0x00CD + "V"
$font = New-Object System.Drawing.Font("Segoe UI", 64, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fmt = New-Object System.Drawing.StringFormat
$fmt.Alignment = [System.Drawing.StringAlignment]::Center
$g.DrawString($text, $font, (New-Object System.Drawing.SolidBrush($white)), (New-Object System.Drawing.RectangleF(0, 370, $size, 90)), $fmt)
$g.Dispose()
$bmp.Save((Join-Path $root "icon.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

# ---------------- fanart.jpg
$W = 1920; $H = 1080
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
Set-Quality $g
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    (New-Object System.Drawing.Point(0, 0)), (New-Object System.Drawing.Point($W, $H)), $navyDark, $navy)
$g.FillRectangle($bg, 0, 0, $W, $H)
# jemný „filmový pás“ dole
$strip = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(22, 255, 255, 255))
for ($i = 0; $i -lt 40; $i++) { $g.FillRectangle($strip, $i * 52 + 10, 1000, 30, 40) }
for ($i = 0; $i -lt 40; $i++) { $g.FillRectangle($strip, $i * 52 + 10, 40, 30, 40) }
Draw-TV $g 1380 230 700 60
$g.Dispose()
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$params = New-Object System.Drawing.Imaging.EncoderParameters(1)
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]88)
$bmp.Save((Join-Path $root "fanart.jpg"), $codec, $params)
$bmp.Dispose()
Write-Output "icon.png a fanart.jpg vygenerované v $root"
