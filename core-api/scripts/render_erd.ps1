param(
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\docs\er-diagram.png')
)

# This renderer uses only Windows System.Drawing, so a contributor can refresh
# the PNG without Graphviz or a separate drawing editor.
Add-Type -AssemblyName System.Drawing

$width = 3200
$height = 2050
$canvas = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($canvas)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

$background = [System.Drawing.ColorTranslator]::FromHtml('#17090d')
$tableBody = [System.Drawing.ColorTranslator]::FromHtml('#fff9e9')
$fieldText = [System.Drawing.ColorTranslator]::FromHtml('#352226')
$accent = [System.Drawing.ColorTranslator]::FromHtml('#8f0010')
$edge = [System.Drawing.ColorTranslator]::FromHtml('#d5a52f')
$line = [System.Drawing.ColorTranslator]::FromHtml('#9c6068')
$muted = [System.Drawing.ColorTranslator]::FromHtml('#f5ddb0')
$g.Clear($background)

$titleFont = New-Object System.Drawing.Font('Segoe UI Semibold', 42, [System.Drawing.FontStyle]::Bold)
$subTitleFont = New-Object System.Drawing.Font('Segoe UI', 20)
$headerFont = New-Object System.Drawing.Font('Segoe UI Semibold', 20, [System.Drawing.FontStyle]::Bold)
$fieldFont = New-Object System.Drawing.Font('Consolas', 16)
$tagFont = New-Object System.Drawing.Font('Segoe UI Semibold', 12, [System.Drawing.FontStyle]::Bold)
$relationFont = New-Object System.Drawing.Font('Segoe UI Semibold', 13, [System.Drawing.FontStyle]::Bold)

$g.DrawString('MATCHMAKER · ER-ДИАГРАММА БАЗЫ ДАННЫХ', $titleFont, (New-Object System.Drawing.SolidBrush $muted), 90, 42)
$g.DrawString('PostgreSQL / SQLAlchemy / Alembic · PK — первичный ключ · FK — внешний ключ · UQ — уникальное ограничение', $subTitleFont, (New-Object System.Drawing.SolidBrush '#d8b8a4'), 93, 108)

function New-Table {
    param(
        [string]$Name,
        [int]$X,
        [int]$Y,
        [string[]]$Fields,
        [int]$Width = 330
    )
    $headerHeight = 46
    $rowHeight = 29
    $height = $headerHeight + ($Fields.Count * $rowHeight)
    $rect = New-Object System.Drawing.Rectangle $X, $Y, $Width, $height
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $tableBody), $rect)
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $accent), $X, $Y, $Width, $headerHeight)
    $g.DrawRectangle((New-Object System.Drawing.Pen $muted, 2), $rect)
    $g.DrawString($Name.ToUpper(), $headerFont, [System.Drawing.Brushes]::White, $X + 13, $Y + 10)
    for ($i = 0; $i -lt $Fields.Count; $i++) {
        $rowY = $Y + $headerHeight + ($i * $rowHeight)
        $g.DrawLine((New-Object System.Drawing.Pen '#d9c7a0', 1), $X, $rowY, $X + $Width, $rowY)
        $parts = $Fields[$i] -split '\|', 2
        $g.DrawString($parts[0], $fieldFont, (New-Object System.Drawing.SolidBrush $fieldText), $X + 12, $rowY + 5)
        if ($parts.Count -gt 1) {
            $tagSize = $g.MeasureString($parts[1], $tagFont)
            $tagX = $X + $Width - $tagSize.Width - 13
            $tagX = [Math]::Max($tagX, $X + 205)
            $g.DrawString($parts[1], $tagFont, (New-Object System.Drawing.SolidBrush $accent), $tagX, $rowY + 7)
        }
    }
    return @{ X = $X; Y = $Y; Width = $Width; Height = $height; Right = $X + $Width; Bottom = $Y + $height; CenterX = $X + [int]($Width / 2); CenterY = $Y + [int]($height / 2) }
}

function Connect {
    param(
        $From,
        $To,
        [string]$Label,
        [string]$FromSide = 'right',
        [string]$ToSide = 'left',
        [int]$Offset = 0
    )
    switch ($FromSide) {
        'left' { $x1 = $From.X; $y1 = $From.CenterY + $Offset }
        'right' { $x1 = $From.Right; $y1 = $From.CenterY + $Offset }
        'top' { $x1 = $From.CenterX + $Offset; $y1 = $From.Y }
        default { $x1 = $From.CenterX + $Offset; $y1 = $From.Bottom }
    }
    switch ($ToSide) {
        'left' { $x2 = $To.X; $y2 = $To.CenterY + $Offset }
        'right' { $x2 = $To.Right; $y2 = $To.CenterY + $Offset }
        'top' { $x2 = $To.CenterX + $Offset; $y2 = $To.Y }
        default { $x2 = $To.CenterX + $Offset; $y2 = $To.Bottom }
    }
    $midX = [int](($x1 + $x2) / 2)
    $pen = New-Object System.Drawing.Pen($line, 2)
    $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
    $g.DrawLine($pen, $x1, $y1, $midX, $y1)
    $g.DrawLine($pen, $midX, $y1, $midX, $y2)
    $g.DrawLine($pen, $midX, $y2, $x2, $y2)
    $pen.Dispose()
    $g.FillEllipse((New-Object System.Drawing.SolidBrush $edge), $x1 - 5, $y1 - 5, 10, 10)
    $g.FillEllipse((New-Object System.Drawing.SolidBrush $edge), $x2 - 5, $y2 - 5, 10, 10)
    $textX = $midX + 8
    $textY = [Math]::Min($y1, $y2) + 4
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $background), $textX - 4, $textY - 2, 126, 24)
    $g.DrawString($Label, $relationFont, (New-Object System.Drawing.SolidBrush $edge), $textX, $textY)
}

$users = New-Table 'users' 120 230 @(
    'id : bigint|PK', 'username : varchar(30)|UQ', 'email : varchar(254)|UQ',
    'hashed_password : varchar(255)', 'is_active : boolean', 'is_verified : boolean',
    'is_admin : boolean', 'token_version : integer', 'created_at : timestamptz'
)
$profiles = New-Table 'profiles' 120 690 @(
    'id : bigint|PK', 'user_id : bigint|FK, UQ', 'first_name : varchar(80)',
    'last_name : varchar(80)', 'bio : text', 'birth_date : date?',
    'github_url : varchar(300)?', 'experience : text', 'interests : text', 'role_id : bigint?|FK'
)
$roles = New-Table 'roles' 580 795 @('id : bigint|PK', 'name : varchar(80)|UQ')
$skills = New-Table 'skills' 1130 190 @('id : bigint|PK', 'name : varchar(80)|UQ')
$profileSkills = New-Table 'profile_skills' 1010 580 @('profile_id : bigint|PK, FK', 'skill_id : bigint|PK, FK', 'level : integer|1..5')
$projects = New-Table 'projects' 2050 230 @(
    'id : bigint|PK', 'owner_id : bigint|FK', 'title : varchar(150)', 'description : text',
    'status : varchar(20)', 'created_at : timestamptz'
)
$projectSkills = New-Table 'project_skills' 1650 690 @('project_id : bigint|PK, FK', 'skill_id : bigint|PK, FK', 'weight : integer|1..5')
$projectRoles = New-Table 'project_roles' 2350 720 @('project_id : bigint|PK, FK', 'role_id : bigint|PK, FK')
$emailCodes = New-Table 'email_codes' 120 1380 @('user_id : bigint|PK, FK', 'purpose : varchar(20)|PK', 'digest : varchar(64)', 'expires_at : bigint', 'attempts : integer')
$sessions = New-Table 'refresh_sessions' 620 1380 @('id : varchar(64)|PK', 'user_id : bigint|FK', 'expires_at : bigint', 'revoked : boolean')
$members = New-Table 'project_members' 1300 1390 @('project_id : bigint|PK, FK', 'user_id : bigint|PK, FK', 'joined_at : timestamptz')
$swipes = New-Table 'swipes' 1840 1160 @(
    'id : bigint|PK', 'project_id : bigint|FK', 'candidate_id : bigint|FK',
    'actor_id : bigint|FK', 'direction : varchar(30)', 'decision : varchar(10)', 'created_at : timestamptz'
)
$matches = New-Table 'matches' 2460 1330 @('id : bigint|PK', 'project_id : bigint|FK', 'candidate_id : bigint|FK', 'created_at : timestamptz')

Connect $users $profiles '1 : 1 (account)' 'bottom' 'top' -95
Connect $profiles $roles 'N : 1 (role)' 'right' 'left' 10
Connect $profiles $profileSkills '1 : N (skills)' 'right' 'left' -55
Connect $skills $profileSkills '1 : N' 'bottom' 'top' -70
Connect $users $projects '1 : N (owner)' 'right' 'left' -150
Connect $projects $projectSkills '1 : N (requirements)' 'bottom' 'top' -65
Connect $skills $projectSkills '1 : N' 'bottom' 'top' 50
Connect $projects $projectRoles '1 : N (roles)' 'right' 'left' 60
Connect $roles $projectRoles '1 : N' 'right' 'left' -30
Connect $users $emailCodes '1 : N (codes)' 'bottom' 'top' -45
Connect $users $sessions '1 : N (sessions)' 'bottom' 'top' 95
Connect $projects $members '1 : N (members)' 'bottom' 'top' -120
Connect $users $members '1 : N' 'bottom' 'top' 105
Connect $projects $swipes '1 : N' 'bottom' 'top' 90
Connect $users $swipes '1 : N (actor/candidate)' 'right' 'left' 100
Connect $projects $matches '1 : N' 'bottom' 'top' 105
Connect $users $matches '1 : N (candidate)' 'right' 'left' 170

$legendX = 2080
$legendY = 1730
$g.DrawRectangle((New-Object System.Drawing.Pen $muted, 1), $legendX, $legendY, 965, 170)
$g.DrawString('Смысл связей', $headerFont, (New-Object System.Drawing.SolidBrush $muted), $legendX + 22, $legendY + 18)
$g.DrawString('Пунктирная линия показывает внешний ключ.  «1 : N» — один объект связан с несколькими.', $subTitleFont, (New-Object System.Drawing.SolidBrush '#ead6b2'), $legendX + 22, $legendY + 65)
$g.DrawString('Например: один пользователь может создать много проектов; один проект требует много навыков.', $subTitleFont, (New-Object System.Drawing.SolidBrush '#ead6b2'), $legendX + 22, $legendY + 105)

$directory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$canvas.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$canvas.Dispose()
Write-Host "ER diagram saved to $OutputPath"
