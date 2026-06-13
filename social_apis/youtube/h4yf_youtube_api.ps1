# h4yf_youtube_api.ps1
# YouTube Data API v3 + YouTube Analytics API integration for HEAT4YAFEAT
# PS 5.1 | Requires: YouTube Data API v3 and YouTube Analytics API enabled in GCP 1070004533548
# First run: -Action Auth (opens browser for Bill's YouTube account)
# Secrets: C:\Users\JAP\.h4yf_secrets\google_oauth_client_aure.json
#          C:\Users\JAP\.h4yf_secrets\youtube_token.json (created on first auth)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Auth','GetChannel','ListVideos','GetVideo','SetPrivacy','UpdateMetadata','UploadVideo','GetAnalytics')]
    [string]$Action = 'GetChannel',

    [string]$VideoId,
    [string]$VideoFile,
    [string]$Title,
    [string]$Description,
    [string]$Tags,       # comma-separated
    [ValidateSet('public','private','unlisted')]
    [string]$Privacy = 'private',
    [string]$StartDate = '2020-01-01',  # for analytics
    [string]$EndDate = (Get-Date -Format 'yyyy-MM-dd')
)

$SecretsDir  = "C:\Users\JAP\.h4yf_secrets"
$OAuthFile   = "$SecretsDir\google_oauth_client_aure.json"
$TokenFile   = "$SecretsDir\youtube_token.json"
$LogFile     = "$env:USERPROFILE\.claude\projects\C--Users-JAP\harness-log.jsonl"

$YT_BASE     = "https://www.googleapis.com/youtube/v3"
$YTA_BASE    = "https://youtubeanalytics.googleapis.com/v2"
$UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"
$TOKEN_URL   = "https://oauth2.googleapis.com/token"

$SCOPES = @(
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
) -join " "

# ── helpers ─────────────────────────────────────────────────────────────────

function Write-Log ($action, $status, $detail = '') {
    $entry = [ordered]@{
        timestamp = (Get-Date -Format 'o')
        action    = "youtube/$action"
        status    = $status
        detail    = $detail
    }
    $entry | ConvertTo-Json -Compress | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Get-OAuthClient {
    if (-not (Test-Path $OAuthFile)) {
        throw "OAuth client file not found: $OAuthFile`nDownload from GCP Console → APIs & Services → Credentials"
    }
    $raw = Get-Content $OAuthFile -Raw | ConvertFrom-Json
    return $raw.installed
}

function Get-AccessToken {
    if (-not (Test-Path $TokenFile)) { return $null }
    $tok = Get-Content $TokenFile -Raw | ConvertFrom-Json
    # return token if it has > 60 seconds of life remaining
    $expiry = [datetime]::Parse($tok.expiry_utc)
    if ($expiry -gt (Get-Date).AddSeconds(60)) {
        return $tok.access_token
    }
    # attempt refresh
    $client = Get-OAuthClient
    try {
        $body = "client_id=$([Uri]::EscapeDataString($client.client_id))&client_secret=$([Uri]::EscapeDataString($client.client_secret))&refresh_token=$([Uri]::EscapeDataString($tok.refresh_token))&grant_type=refresh_token"
        $r = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
        $tok.access_token = $r.access_token
        $tok.expiry_utc   = (Get-Date).AddSeconds($r.expires_in).ToString('o')
        $tok | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8
        return $r.access_token
    } catch {
        Write-Warning "Token refresh failed: $_"
        return $null
    }
}

function Invoke-Auth {
    $client = Get-OAuthClient
    $port   = 8080
    $redirectUri = "http://localhost:$port/"
    $state  = [System.Guid]::NewGuid().ToString('N')

    $authUrl = "https://accounts.google.com/o/oauth2/v2/auth?" +
        "client_id=$([Uri]::EscapeDataString($client.client_id))" +
        "&redirect_uri=$([Uri]::EscapeDataString($redirectUri))" +
        "&response_type=code" +
        "&scope=$([Uri]::EscapeDataString($SCOPES))" +
        "&access_type=offline" +
        "&prompt=consent" +
        "&state=$state"

    # start local listener
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$port/")
    $listener.Start()

    Write-Host "Opening browser for YouTube authorization..." -ForegroundColor Cyan
    Write-Host "Log in as Bill's YouTube account (b2ill2323@gmail.com)" -ForegroundColor Yellow
    Start-Process $authUrl

    $ctx  = $listener.GetContext()
    $qs   = [System.Web.HttpUtility]::ParseQueryString($ctx.Request.Url.Query)
    $code = $qs['code']

    $html = "<html><body style='font-family:sans-serif;padding:40px'><h2>H4YF YouTube Auth Complete</h2><p>You can close this tab.</p></body></html>"
    $buf  = [Text.Encoding]::UTF8.GetBytes($html)
    $ctx.Response.ContentLength64 = $buf.Length
    $ctx.Response.OutputStream.Write($buf, 0, $buf.Length)
    $ctx.Response.Close()
    $listener.Stop()

    if (-not $code) { throw "No authorization code received" }

    # exchange code for tokens
    $body = "code=$([Uri]::EscapeDataString($code))&client_id=$([Uri]::EscapeDataString($client.client_id))&client_secret=$([Uri]::EscapeDataString($client.client_secret))&redirect_uri=$([Uri]::EscapeDataString($redirectUri))&grant_type=authorization_code"
    $r = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"

    $tok = @{
        access_token  = $r.access_token
        refresh_token = $r.refresh_token
        expiry_utc    = (Get-Date).AddSeconds($r.expires_in).ToString('o')
        scope         = $r.scope
    }
    $tok | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8
    Write-Host "Token saved to $TokenFile" -ForegroundColor Green
    Write-Log 'Auth' 'OK' 'tokens saved'
    return $r.access_token
}

function Invoke-YT ($path, $method = 'GET', $body = $null, $params = @{}) {
    $token = Get-AccessToken
    if (-not $token) { $token = Invoke-Auth }

    $query = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$([Uri]::EscapeDataString($_.Value))" }) -join '&'
    $uri   = "$YT_BASE$path" + $(if ($query) { "?$query" } else { '' })

    $headers = @{ Authorization = "Bearer $token" }
    $splat   = @{ Uri = $uri; Method = $method; Headers = $headers; UseBasicParsing = $true }
    if ($body) {
        $splat.Body        = ($body | ConvertTo-Json -Depth 10)
        $splat.ContentType = 'application/json; charset=utf-8'
    }
    return Invoke-RestMethod @splat
}

function Invoke-YTA ($path, $params = @{}) {
    $token = Get-AccessToken
    if (-not $token) { $token = Invoke-Auth }
    $query = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$([Uri]::EscapeDataString($_.Value))" }) -join '&'
    $uri   = "$YTA_BASE$path?$query"
    return Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $token" } -UseBasicParsing
}

# ── actions ──────────────────────────────────────────────────────────────────

function Get-H4YFChannel {
    Write-Host "Fetching channel info..." -ForegroundColor Cyan
    $r = Invoke-YT '/channels' -params @{
        part  = 'snippet,statistics,contentDetails'
        mine  = 'true'
    }
    if ($r.items.Count -eq 0) { Write-Host "No channel found for this account." -ForegroundColor Red; return }
    $ch = $r.items[0]
    Write-Host ""
    Write-Host "Channel: $($ch.snippet.title)" -ForegroundColor Green
    Write-Host "ID:          $($ch.id)"
    Write-Host "Subscribers: $($ch.statistics.subscriberCount)"
    Write-Host "Videos:      $($ch.statistics.videoCount)"
    Write-Host "Total views: $($ch.statistics.viewCount)"
    Write-Host "Uploads playlist: $($ch.contentDetails.relatedPlaylists.uploads)"
    Write-Log 'GetChannel' 'OK' $ch.id
    return $ch
}

function Get-H4YFVideoList {
    Write-Host "Fetching video list..." -ForegroundColor Cyan
    # get uploads playlist ID first
    $ch = Invoke-YT '/channels' -params @{ part = 'contentDetails'; mine = 'true' }
    $playlistId = $ch.items[0].contentDetails.relatedPlaylists.uploads

    $videos = @()
    $pageToken = ''
    do {
        $p = @{ part = 'snippet'; playlistId = $playlistId; maxResults = '50' }
        if ($pageToken) { $p.pageToken = $pageToken }
        $r = Invoke-YT '/playlistItems' -params $p
        $videos += $r.items
        $pageToken = $r.nextPageToken
    } while ($pageToken)

    # get stats for each video
    $ids = ($videos | ForEach-Object { $_.snippet.resourceId.videoId }) -join ','
    $stats = Invoke-YT '/videos' -params @{ part = 'statistics,status'; id = $ids }
    $statsMap = @{}
    foreach ($v in $stats.items) { $statsMap[$v.id] = $v }

    Write-Host ""
    Write-Host "Videos ($($videos.Count)):" -ForegroundColor Green
    foreach ($v in $videos) {
        $id    = $v.snippet.resourceId.videoId
        $s     = $statsMap[$id]
        $priv  = $s.status.privacyStatus
        $views = $s.statistics.viewCount
        Write-Host "  [$id] $($v.snippet.title)"
        Write-Host "    Privacy: $priv | Views: $views | Published: $($v.snippet.publishedAt.Substring(0,10))"
    }
    Write-Log 'ListVideos' 'OK' "$($videos.Count) videos"
    return $videos
}

function Set-H4YFVideoPrivacy {
    param([string]$Id, [string]$Priv)
    if (-not $Id) { throw "-VideoId is required" }
    Write-Host "Setting $Id → $Priv" -ForegroundColor Cyan
    $r = Invoke-YT '/videos' -method 'PUT' -params @{ part = 'status' } -body @{
        id     = $Id
        status = @{ privacyStatus = $Priv }
    }
    Write-Host "Done: $($r.status.privacyStatus)" -ForegroundColor Green
    Write-Log 'SetPrivacy' 'OK' "$Id -> $Priv"
    return $r
}

function Update-H4YFVideoMetadata {
    param([string]$Id, [string]$Ttl, [string]$Desc, [string]$TagList)
    if (-not $Id) { throw "-VideoId is required" }
    Write-Host "Updating metadata for $Id..." -ForegroundColor Cyan

    # fetch current snippet first (categoryId is required on update)
    $cur = Invoke-YT '/videos' -params @{ part = 'snippet'; id = $Id }
    $snip = $cur.items[0].snippet

    if ($Ttl)  { $snip.title       = $Ttl }
    if ($Desc) { $snip.description = $Desc }
    if ($TagList) { $snip.tags     = $TagList -split ',' | ForEach-Object { $_.Trim() } }

    $r = Invoke-YT '/videos' -method 'PUT' -params @{ part = 'snippet' } -body @{
        id      = $Id
        snippet = $snip
    }
    Write-Host "Updated: $($r.snippet.title)" -ForegroundColor Green
    Write-Log 'UpdateMetadata' 'OK' $Id
    return $r
}

function Add-H4YFVideo {
    param([string]$File, [string]$Ttl, [string]$Desc, [string]$Priv, [string]$TagList)
    if (-not $File -or -not (Test-Path $File)) { throw "Video file not found: $File" }
    if (-not $Ttl)  { throw "-Title is required" }

    $token = Get-AccessToken
    if (-not $token) { $token = Invoke-Auth }

    $tags = if ($TagList) { $TagList -split ',' | ForEach-Object { $_.Trim() } } else { @() }

    $meta = @{
        snippet = @{
            title       = $Ttl
            description = if ($Desc) { $Desc } else { '' }
            tags        = $tags
            categoryId  = '26'   # howto & style
        }
        status = @{ privacyStatus = if ($Priv) { $Priv } else { 'private' } }
    } | ConvertTo-Json -Depth 10

    $fileBytes = [IO.File]::ReadAllBytes($File)
    $mimeType  = if ($File -match '\.mp4$') { 'video/mp4' } elseif ($File -match '\.mov$') { 'video/quicktime' } else { 'video/mp4' }
    $fileSize  = $fileBytes.Length

    Write-Host "Initiating resumable upload ($([Math]::Round($fileSize/1MB,1)) MB)..." -ForegroundColor Cyan

    # initiate upload session
    $initResp = Invoke-WebRequest `
        -Uri "$UPLOAD_BASE/videos?uploadType=resumable&part=snippet,status" `
        -Method POST `
        -Headers @{
            Authorization            = "Bearer $token"
            'X-Upload-Content-Type'  = $mimeType
            'X-Upload-Content-Length'= $fileSize
        } `
        -Body $meta `
        -ContentType 'application/json; charset=utf-8' `
        -UseBasicParsing
    $uploadUrl = $initResp.Headers.Location

    # upload in 10 MB chunks
    $chunkSize = 10 * 1024 * 1024
    $offset    = 0
    $result    = $null

    while ($offset -lt $fileSize) {
        $end       = [Math]::Min($offset + $chunkSize - 1, $fileSize - 1)
        $chunkLen  = $end - $offset + 1
        $chunk     = $fileBytes[$offset..$end]

        $pct = [Math]::Round(($offset / $fileSize) * 100)
        Write-Progress -Activity "Uploading" -Status "$pct% ($([Math]::Round($offset/1MB,1))/$([Math]::Round($fileSize/1MB,1)) MB)" -PercentComplete $pct

        try {
            $result = Invoke-RestMethod `
                -Uri $uploadUrl `
                -Method PUT `
                -Headers @{
                    Authorization   = "Bearer $token"
                    'Content-Range' = "bytes $offset-$end/$fileSize"
                } `
                -Body $chunk `
                -ContentType $mimeType
        } catch {
            if ($_.Exception.Response.StatusCode.value__ -eq 308) {
                # Resume Incomplete — normal for chunked upload
            } else {
                throw
            }
        }
        $offset += $chunkLen
    }
    Write-Progress -Activity "Uploading" -Completed

    Write-Host "Upload complete: $($result.id)" -ForegroundColor Green
    Write-Host "  Title:   $($result.snippet.title)"
    Write-Host "  Privacy: $($result.status.privacyStatus)"
    Write-Log 'UploadVideo' 'OK' $result.id
    return $result
}

function Get-H4YFAnalytics {
    param([string]$Id, [string]$Start, [string]$End)
    Write-Host "Fetching analytics for $Id ($Start → $End)..." -ForegroundColor Cyan

    $ch = Invoke-YT '/channels' -params @{ part = 'id'; mine = 'true' }
    $channelId = $ch.items[0].id

    $filter = if ($Id) { "video==$Id" } else { "channel==$channelId" }

    $r = Invoke-YTA '/reports' -params @{
        ids        = "channel==$channelId"
        startDate  = $Start
        endDate    = $End
        metrics    = 'views,estimatedMinutesWatched,averageViewDuration,likes,shares,subscribersGained'
        filters    = $filter
        dimensions = 'day'
        sort       = 'day'
    }

    if ($r.rows) {
        Write-Host ""
        Write-Host "Date         Views  Watch(min)  AvgDur  Likes  Shares  Subs+" -ForegroundColor Green
        Write-Host "------------ -----  ----------  ------  -----  ------  -----"
        foreach ($row in $r.rows) {
            Write-Host ("{0,-12}  {1,5}  {2,10}  {3,6}  {4,5}  {5,6}  {6,5}" -f $row[0],$row[1],$row[2],$row[3],$row[4],$row[5],$row[6])
        }
    } else {
        Write-Host "No analytics data for this range." -ForegroundColor Yellow
    }
    Write-Log 'GetAnalytics' 'OK' "filter=$filter start=$Start end=$End"
    return $r
}

# ── dispatch ──────────────────────────────────────────────────────────────────

Add-Type -AssemblyName System.Web

switch ($Action) {
    'Auth'           { Invoke-Auth | Out-Null; Write-Host "Auth complete." -ForegroundColor Green }
    'GetChannel'     { Get-H4YFChannel | Out-Null }
    'ListVideos'     { Get-H4YFVideoList | Out-Null }
    'GetVideo'       { (Invoke-YT '/videos' -params @{ part='snippet,statistics,status'; id=$VideoId }).items | ConvertTo-Json -Depth 5 | Write-Host }
    'SetPrivacy'     { Set-H4YFVideoPrivacy -Id $VideoId -Priv $Privacy | Out-Null }
    'UpdateMetadata' { Update-H4YFVideoMetadata -Id $VideoId -Ttl $Title -Desc $Description -TagList $Tags | Out-Null }
    'UploadVideo'    { Add-H4YFVideo -File $VideoFile -Ttl $Title -Desc $Description -Priv $Privacy -TagList $Tags | Out-Null }
    'GetAnalytics'   { Get-H4YFAnalytics -Id $VideoId -Start $StartDate -End $EndDate | Out-Null }
}
