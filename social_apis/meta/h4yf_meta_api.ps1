# h4yf_meta_api.ps1
# Meta Graph API v18 — Instagram Business + Facebook Page for HEAT4YAFEAT
# PS 5.1 | Requires a Facebook App (see SETUP_GUIDE.md step 2)
# First run: -Action Auth (opens browser — log in as Bill)
# Secrets: C:\Users\JAP\.h4yf_secrets\meta_app_credentials.json  (manual — App ID + Secret)
#          C:\Users\JAP\.h4yf_secrets\meta_tokens.json            (created on first auth)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Auth','GetAccounts','GetIGAccount','PostIGPhoto','PublishIGReel','PostFBPage','PostFBGroup','GetIGInsights','GetPageInsights')]
    [string]$Action = 'GetAccounts',

    [string]$ImageUrl,      # public URL for photo posts
    [string]$VideoFile,     # local path for reel/video
    [string]$VideoUrl,      # public URL alternative for video
    [string]$Caption,
    [string]$GroupId,       # Facebook Group ID for PostFBGroup
    [string]$Message,       # for FB posts
    [ValidateSet('day','week','month')]
    [string]$Period = 'day',
    [string]$Since,
    [string]$Until
)

$SecretsDir  = "C:\Users\JAP\.h4yf_secrets"
$CredsFile   = "$SecretsDir\meta_app_credentials.json"
$TokenFile   = "$SecretsDir\meta_tokens.json"
$LogFile     = "$env:USERPROFILE\.claude\projects\C--Users-JAP\harness-log.jsonl"

$GRAPH       = "https://graph.facebook.com/v18.0"
$TOKEN_URL   = "$GRAPH/oauth/access_token"

$SCOPES = @(
    'instagram_basic',
    'instagram_content_publish',
    'instagram_manage_insights',
    'pages_read_engagement',
    'pages_manage_posts',
    'pages_show_list',
    'business_management',
    'public_profile'
) -join ','

# ── helpers ──────────────────────────────────────────────────────────────────

function Write-Log ($action, $status, $detail = '') {
    $entry = [ordered]@{
        timestamp = (Get-Date -Format 'o')
        action    = "meta/$action"
        status    = $status
        detail    = $detail
    }
    $entry | ConvertTo-Json -Compress | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Get-AppCreds {
    if (-not (Test-Path $CredsFile)) {
        throw "Meta app credentials not found: $CredsFile`nCreate it per SETUP_GUIDE.md step 2D."
    }
    return Get-Content $CredsFile -Raw | ConvertFrom-Json
}

function Get-Tokens {
    if (-not (Test-Path $TokenFile)) { return $null }
    return Get-Content $TokenFile -Raw | ConvertFrom-Json
}

function Invoke-Auth {
    $app    = Get-AppCreds
    $port   = 8080
    $redirectUri = "http://localhost:$port/"
    $state  = [System.Guid]::NewGuid().ToString('N')

    $authUrl = "https://www.facebook.com/v18.0/dialog/oauth?" +
        "client_id=$($app.app_id)" +
        "&redirect_uri=$([Uri]::EscapeDataString($redirectUri))" +
        "&scope=$([Uri]::EscapeDataString($SCOPES))" +
        "&state=$state" +
        "&response_type=code"

    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$port/")
    $listener.Start()

    Write-Host "Opening browser for Meta/Facebook authorization..." -ForegroundColor Cyan
    Write-Host "Log in as Bill (b2ill2323@gmail.com) and authorize the H4YF app." -ForegroundColor Yellow
    Start-Process $authUrl

    $ctx  = $listener.GetContext()
    $qs   = [System.Web.HttpUtility]::ParseQueryString($ctx.Request.Url.Query)
    $code = $qs['code']

    $html = "<html><body style='font-family:sans-serif;padding:40px'><h2>H4YF Meta Auth Complete</h2><p>You can close this tab.</p></body></html>"
    $buf  = [Text.Encoding]::UTF8.GetBytes($html)
    $ctx.Response.ContentLength64 = $buf.Length
    $ctx.Response.OutputStream.Write($buf, 0, $buf.Length)
    $ctx.Response.Close()
    $listener.Stop()

    if (-not $code) { throw "No authorization code received — check browser for errors" }

    # short-lived user token
    $r = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body @{
        client_id     = $app.app_id
        client_secret = $app.app_secret
        redirect_uri  = $redirectUri
        code          = $code
    }

    # exchange for long-lived user token (~60 days)
    $ll = Invoke-RestMethod -Uri "$TOKEN_URL?grant_type=fb_exchange_token&client_id=$($app.app_id)&client_secret=$($app.app_secret)&fb_exchange_token=$($r.access_token)"
    $userToken = $ll.access_token

    # get pages and IG account
    $pages = Invoke-RestMethod -Uri "$GRAPH/me/accounts?access_token=$userToken&fields=id,name,access_token,instagram_business_account"

    $tok = @{
        user_token      = $userToken
        user_id         = $null
        pages           = @()
        ig_account_id   = $null
        ig_username     = $null
    }

    # get user ID
    $me = Invoke-RestMethod -Uri "$GRAPH/me?access_token=$userToken&fields=id,name"
    $tok.user_id = $me.id

    foreach ($page in $pages.data) {
        $pageInfo = @{
            page_id      = $page.id
            page_name    = $page.name
            page_token   = $page.access_token   # never-expiring page token
        }
        if ($page.instagram_business_account) {
            $igId = $page.instagram_business_account.id
            $igInfo = Invoke-RestMethod -Uri "$GRAPH/$igId?fields=id,username,name&access_token=$($page.access_token)"
            $pageInfo.ig_account_id = $igId
            $pageInfo.ig_username   = $igInfo.username
            if (-not $tok.ig_account_id) {
                $tok.ig_account_id = $igId
                $tok.ig_username   = $igInfo.username
            }
        }
        $tok.pages += $pageInfo
    }

    $tok | ConvertTo-Json -Depth 5 | Set-Content $TokenFile -Encoding UTF8
    Write-Host ""
    Write-Host "Auth complete. Saved to $TokenFile" -ForegroundColor Green
    Write-Host "  User: $($me.name) (ID: $($me.id))"
    foreach ($p in $tok.pages) {
        Write-Host "  Page: $($p.page_name) (ID: $($p.page_id))"
        if ($p.ig_account_id) {
            Write-Host "    Instagram: @$($p.ig_username) (ID: $($p.ig_account_id))"
        }
    }
    Write-Log 'Auth' 'OK' "user=$($me.id) pages=$($tok.pages.Count)"
    return $tok
}

function Get-PageToken ([string]$pageId = $null) {
    $tok = Get-Tokens
    if (-not $tok) { throw "Not authenticated. Run: -Action Auth" }
    if (-not $pageId -or $tok.pages.Count -eq 1) { return $tok.pages[0] }
    $p = $tok.pages | Where-Object { $_.page_id -eq $pageId }
    if (-not $p) { throw "Page ID $pageId not found in saved tokens" }
    return $p
}

function Get-IGAccountId {
    $tok = Get-Tokens
    if (-not $tok) { throw "Not authenticated. Run: -Action Auth" }
    if (-not $tok.ig_account_id) { throw "No Instagram Business Account found. Connect Instagram to a Facebook Page." }
    return $tok.ig_account_id
}

function Get-UserToken {
    $tok = Get-Tokens
    if (-not $tok) { throw "Not authenticated. Run: -Action Auth" }
    return $tok.user_token
}

# ── upload helper (for large video files) ─────────────────────────────────────

function Invoke-GraphMultipart ($uri, $filePath, $extraFields = @{}) {
    # PS 5.1 multipart upload using WebClient workaround
    $boundary = [Guid]::NewGuid().ToString('N')
    $ms       = New-Object IO.MemoryStream

    # add extra fields
    foreach ($kv in $extraFields.GetEnumerator()) {
        $part = "--$boundary`r`nContent-Disposition: form-data; name=`"$($kv.Key)`"`r`n`r`n$($kv.Value)`r`n"
        $bytes = [Text.Encoding]::UTF8.GetBytes($part)
        $ms.Write($bytes, 0, $bytes.Length)
    }

    # add file
    $fileName = Split-Path $filePath -Leaf
    $mime     = if ($filePath -match '\.mp4$') { 'video/mp4' } elseif ($filePath -match '\.mov$') { 'video/quicktime' } else { 'video/mp4' }
    $header   = "--$boundary`r`nContent-Disposition: form-data; name=`"video_file`"; filename=`"$fileName`"`r`nContent-Type: $mime`r`n`r`n"
    $hBytes   = [Text.Encoding]::UTF8.GetBytes($header)
    $ms.Write($hBytes, 0, $hBytes.Length)
    $fBytes   = [IO.File]::ReadAllBytes($filePath)
    $ms.Write($fBytes, 0, $fBytes.Length)
    $tail     = "`r`n--$boundary--`r`n"
    $tBytes   = [Text.Encoding]::UTF8.GetBytes($tail)
    $ms.Write($tBytes, 0, $tBytes.Length)

    $body = $ms.ToArray()
    $ms.Dispose()

    $resp = Invoke-RestMethod -Uri $uri -Method POST `
        -Body $body `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -UseBasicParsing
    return $resp
}

# ── actions ──────────────────────────────────────────────────────────────────

function Get-H4YFAccounts {
    Write-Host "Fetching linked Facebook Pages and Instagram accounts..." -ForegroundColor Cyan
    $tok = Get-Tokens
    if (-not $tok) { throw "Not authenticated. Run: -Action Auth" }
    Write-Host ""
    foreach ($p in $tok.pages) {
        Write-Host "Facebook Page: $($p.page_name) (ID: $($p.page_id))" -ForegroundColor Green
        if ($p.ig_account_id) {
            Write-Host "  Instagram:   @$($p.ig_username) (ID: $($p.ig_account_id))"
        } else {
            Write-Host "  Instagram:   (not connected)" -ForegroundColor Yellow
        }
    }
    return $tok
}

function Publish-H4YFIGPhoto {
    param([string]$Url, [string]$Cap)
    if (-not $Url) { throw "-ImageUrl is required (must be a public URL)" }

    $igId      = Get-IGAccountId
    $pageInfo  = Get-PageToken
    $pageToken = $pageInfo.page_token

    Write-Host "Creating IG photo container..." -ForegroundColor Cyan
    $container = Invoke-RestMethod -Uri "$GRAPH/$igId/media" -Method POST -Body @{
        image_url    = $Url
        caption      = if ($Cap) { $Cap } else { '' }
        access_token = $pageToken
    }

    Write-Host "Publishing..." -ForegroundColor Cyan
    $result = Invoke-RestMethod -Uri "$GRAPH/$igId/media_publish" -Method POST -Body @{
        creation_id  = $container.id
        access_token = $pageToken
    }

    Write-Host "Published! Post ID: $($result.id)" -ForegroundColor Green
    Write-Log 'PostIGPhoto' 'OK' $result.id
    return $result
}

function Publish-H4YFIGReel {
    param([string]$VidUrl, [string]$VidFile, [string]$Cap)

    $igId      = Get-IGAccountId
    $pageInfo  = Get-PageToken
    $pageToken = $pageInfo.page_token

    if ($VidUrl) {
        # URL-based (easier — host the video publicly first)
        Write-Host "Creating Reel container from URL..." -ForegroundColor Cyan
        $container = Invoke-RestMethod -Uri "$GRAPH/$igId/media" -Method POST -Body @{
            video_url    = $VidUrl
            media_type   = 'REELS'
            caption      = if ($Cap) { $Cap } else { '' }
            access_token = $pageToken
        }
    } elseif ($VidFile -and (Test-Path $VidFile)) {
        # Upload via resumable session
        Write-Host "Initiating video upload session..." -ForegroundColor Cyan
        $session = Invoke-RestMethod -Uri "$GRAPH/$igId/media" -Method POST -Body @{
            media_type   = 'REELS'
            caption      = if ($Cap) { $Cap } else { '' }
            upload_type  = 'resumable'
            access_token = $pageToken
        }
        $uploadId = $session.id
        $uploadUrl = $session.uri

        # upload file
        Write-Host "Uploading video file ($([Math]::Round((Get-Item $VidFile).Length/1MB,1)) MB)..." -ForegroundColor Cyan
        $fileBytes = [IO.File]::ReadAllBytes($VidFile)
        Invoke-RestMethod -Uri $uploadUrl -Method POST `
            -Headers @{ Authorization = "OAuth $pageToken"; 'offset' = '0'; 'file_size' = $fileBytes.Length } `
            -Body $fileBytes -ContentType 'application/octet-stream' | Out-Null

        $container = @{ id = $uploadId }
    } else {
        throw "Provide either -VideoUrl (public URL) or -VideoFile (local path)"
    }

    # poll until processing done
    Write-Host "Waiting for video processing..." -ForegroundColor Cyan
    $attempts = 0
    do {
        Start-Sleep -Seconds 5
        $status = Invoke-RestMethod -Uri "$GRAPH/$($container.id)?fields=status_code&access_token=$pageToken"
        $attempts++
        Write-Host "  Status: $($status.status_code) ($attempts)"
    } while ($status.status_code -ne 'FINISHED' -and $attempts -lt 60)

    if ($status.status_code -ne 'FINISHED') {
        throw "Video processing timed out. Status: $($status.status_code)"
    }

    Write-Host "Publishing Reel..." -ForegroundColor Cyan
    $result = Invoke-RestMethod -Uri "$GRAPH/$igId/media_publish" -Method POST -Body @{
        creation_id  = $container.id
        access_token = $pageToken
    }

    Write-Host "Reel published! Post ID: $($result.id)" -ForegroundColor Green
    Write-Log 'PublishIGReel' 'OK' $result.id
    return $result
}

function Publish-H4YFFBPage {
    param([string]$Msg)
    if (-not $Msg) { throw "-Message is required" }
    $pageInfo = Get-PageToken
    Write-Host "Posting to Facebook Page: $($pageInfo.page_name)..." -ForegroundColor Cyan
    $result = Invoke-RestMethod -Uri "$GRAPH/$($pageInfo.page_id)/feed" -Method POST -Body @{
        message      = $Msg
        access_token = $pageInfo.page_token
    }
    Write-Host "Posted! Post ID: $($result.id)" -ForegroundColor Green
    Write-Log 'PostFBPage' 'OK' $result.id
    return $result
}

function Publish-H4YFFBGroup {
    param([string]$GId, [string]$Msg)
    if (-not $GId) { throw "-GroupId is required (get from group URL: facebook.com/groups/GROUPID)" }
    if (-not $Msg) { throw "-Message is required" }
    $userToken = Get-UserToken
    Write-Host "Posting to Facebook Group $GId..." -ForegroundColor Cyan
    $result = Invoke-RestMethod -Uri "$GRAPH/$GId/feed" -Method POST -Body @{
        message      = $Msg
        access_token = $userToken
    }
    Write-Host "Posted! Post ID: $($result.id)" -ForegroundColor Green
    Write-Log 'PostFBGroup' 'OK' "$GId: $($result.id)"
    return $result
}

function Get-H4YFIGInsights {
    $igId      = Get-IGAccountId
    $pageInfo  = Get-PageToken
    $pageToken = $pageInfo.page_token

    $sinceTs = if ($Since) { [DateTimeOffset]::Parse($Since).ToUnixTimeSeconds() } else { [DateTimeOffset]::UtcNow.AddDays(-28).ToUnixTimeSeconds() }
    $untilTs = if ($Until) { [DateTimeOffset]::Parse($Until).ToUnixTimeSeconds() } else { [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }

    Write-Host "Fetching Instagram insights for @$($pageInfo.ig_username)..." -ForegroundColor Cyan

    $metrics = 'impressions,reach,profile_views,website_clicks,follower_count'
    $r = Invoke-RestMethod -Uri "$GRAPH/$igId/insights?metric=$metrics&period=$Period&since=$sinceTs&until=$untilTs&access_token=$pageToken"

    Write-Host ""
    Write-Host "Instagram Insights (@$($pageInfo.ig_username))" -ForegroundColor Green
    foreach ($m in $r.data) {
        Write-Host "  $($m.name):"
        foreach ($v in $m.values) {
            Write-Host "    $($v.end_time.Substring(0,10)): $($v.value)"
        }
    }
    Write-Log 'GetIGInsights' 'OK' "period=$Period"
    return $r
}

# ── dispatch ──────────────────────────────────────────────────────────────────

Add-Type -AssemblyName System.Web

switch ($Action) {
    'Auth'           { Invoke-Auth | Out-Null }
    'GetAccounts'    { Get-H4YFAccounts | Out-Null }
    'GetIGAccount'   {
        $tok = Get-Tokens
        Write-Host "IG Account: @$($tok.ig_username) (ID: $($tok.ig_account_id))" -ForegroundColor Green
    }
    'PostIGPhoto'    { Publish-H4YFIGPhoto   -Url $ImageUrl -Cap $Caption | Out-Null }
    'PublishIGReel'  { Publish-H4YFIGReel    -VidUrl $VideoUrl -VidFile $VideoFile -Cap $Caption | Out-Null }
    'PostFBPage'     { Publish-H4YFFBPage    -Msg $Message | Out-Null }
    'PostFBGroup'    { Publish-H4YFFBGroup   -GId $GroupId -Msg $Message | Out-Null }
    'GetIGInsights'  { Get-H4YFIGInsights | Out-Null }
    'GetPageInsights'{
        $pageInfo  = Get-PageToken
        $r = Invoke-RestMethod -Uri "$GRAPH/$($pageInfo.page_id)/insights?metric=page_impressions,page_reach,page_fans,page_views_total&period=$Period&access_token=$($pageInfo.page_token)"
        $r.data | ForEach-Object { Write-Host "$($_.name): $(($_.values | Select-Object -Last 1).value)" }
    }
}
