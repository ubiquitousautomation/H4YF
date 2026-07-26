# h4yf_tiktok_api.ps1
# TikTok Content Posting API v2 for HEAT4YAFEAT (@heat4yafeat)
# PS 5.1 | Requires a TikTok Developer App (see SETUP_GUIDE.md step 3)
# First run: -Action Auth (opens browser — log in as @heat4yafeat)
# Secrets: C:\Users\JAP\.h4yf_secrets\tiktok_app_credentials.json  (manual — Client Key + Secret)
#          C:\Users\JAP\.h4yf_secrets\tiktok_tokens.json            (created on first auth)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Auth','GetCreatorInfo','ListVideos','PublishVideo','CheckPublishStatus','GetAnalytics')]
    [string]$Action = 'GetCreatorInfo',

    [string]$VideoFile,
    [string]$Caption,
    [string[]]$PrivacyLevel = 'SELF_ONLY',   # SELF_ONLY | MUTUAL_FOLLOW_FRIENDS | FOLLOWER_OF_CREATOR | PUBLIC_TO_EVERYONE
    [switch]$DisableDuet,
    [switch]$DisableStitch,
    [switch]$DisableComment,
    [string]$PublishId          # for CheckPublishStatus
)

$SecretsDir  = "C:\Users\JAP\.h4yf_secrets"
$CredsFile   = "$SecretsDir\tiktok_app_credentials.json"
$TokenFile   = "$SecretsDir\tiktok_tokens.json"
$LogFile     = "$env:USERPROFILE\.claude\projects\C--Users-JAP\harness-log.jsonl"

$OPEN_API    = "https://open.tiktokapis.com/v2"
$TOKEN_URL   = "$OPEN_API/oauth/token/"
$REVOKE_URL  = "$OPEN_API/oauth/revoke/"

$SCOPES = @(
    'user.info.basic',
    'video.publish',
    'video.list'
) -join ','

# ── helpers ──────────────────────────────────────────────────────────────────

function Write-Log ($action, $status, $detail = '') {
    $entry = [ordered]@{
        timestamp = (Get-Date -Format 'o')
        action    = "tiktok/$action"
        status    = $status
        detail    = $detail
    }
    $entry | ConvertTo-Json -Compress | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Get-AppCreds {
    if (-not (Test-Path $CredsFile)) {
        throw "TikTok app credentials not found: $CredsFile`nCreate it per SETUP_GUIDE.md step 3B."
    }
    return Get-Content $CredsFile -Raw | ConvertFrom-Json
}

function Get-Tokens {
    if (-not (Test-Path $TokenFile)) { return $null }
    return Get-Content $TokenFile -Raw | ConvertFrom-Json
}

function Get-AccessToken {
    $tok = Get-Tokens
    if (-not $tok) { return $null }

    $expiry = [datetime]::Parse($tok.expiry_utc)
    if ($expiry -gt (Get-Date).AddSeconds(60)) { return $tok.access_token }

    # refresh
    $app = Get-AppCreds
    try {
        $r = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body @{
            client_key     = $app.client_key
            client_secret  = $app.client_secret
            grant_type     = 'refresh_token'
            refresh_token  = $tok.refresh_token
        } -ContentType 'application/x-www-form-urlencoded'

        if ($r.data.access_token) {
            $tok.access_token  = $r.data.access_token
            $tok.refresh_token = $r.data.refresh_token
            $tok.expiry_utc    = (Get-Date).AddSeconds($r.data.expires_in).ToString('o')
            $tok | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8
            return $tok.access_token
        }
    } catch {
        Write-Warning "Token refresh failed: $_"
    }
    return $null
}

function Invoke-TT ($path, $method = 'POST', $body = $null) {
    $token = Get-AccessToken
    if (-not $token) { $token = (Invoke-Auth).access_token }

    $headers = @{
        Authorization  = "Bearer $token"
        'Content-Type' = 'application/json; charset=utf-8'
    }
    $splat = @{
        Uri             = "$OPEN_API$path"
        Method          = $method
        Headers         = $headers
        UseBasicParsing = $true
    }
    if ($body) { $splat.Body = $body | ConvertTo-Json -Depth 10 }
    $r = Invoke-RestMethod @splat
    if ($r.error.code -and $r.error.code -ne 'ok') {
        throw "TikTok API error ($($r.error.code)): $($r.error.message)"
    }
    return $r.data
}

# ── auth ──────────────────────────────────────────────────────────────────────

function Invoke-Auth {
    $app    = Get-AppCreds
    $port   = 8080
    $redirectUri = "http://localhost:$port/"
    $state  = [System.Guid]::NewGuid().ToString('N')
    $csrfState = $state

    $authUrl = "https://www.tiktok.com/v2/auth/authorize/?" +
        "client_key=$($app.client_key)" +
        "&scope=$([Uri]::EscapeDataString($SCOPES))" +
        "&response_type=code" +
        "&redirect_uri=$([Uri]::EscapeDataString($redirectUri))" +
        "&state=$csrfState"

    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$port/")
    $listener.Start()

    Write-Host "Opening browser for TikTok authorization..." -ForegroundColor Cyan
    Write-Host "Log in as @heat4yafeat account" -ForegroundColor Yellow
    Start-Process $authUrl

    $ctx  = $listener.GetContext()
    $qs   = [System.Web.HttpUtility]::ParseQueryString($ctx.Request.Url.Query)
    $code = $qs['code']

    $html = "<html><body style='font-family:sans-serif;padding:40px'><h2>H4YF TikTok Auth Complete</h2><p>You can close this tab.</p></body></html>"
    $buf  = [Text.Encoding]::UTF8.GetBytes($html)
    $ctx.Response.ContentLength64 = $buf.Length
    $ctx.Response.OutputStream.Write($buf, 0, $buf.Length)
    $ctx.Response.Close()
    $listener.Stop()

    if (-not $code) { throw "No authorization code received" }

    # exchange code for token
    $r = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body @{
        client_key     = $app.client_key
        client_secret  = $app.client_secret
        code           = $code
        grant_type     = 'authorization_code'
        redirect_uri   = $redirectUri
        code_verifier  = ''
    } -ContentType 'application/x-www-form-urlencoded'

    if ($r.error -and $r.error -ne 'ok') {
        throw "Auth error: $($r.error_description)"
    }

    $tok = @{
        access_token   = $r.data.access_token
        refresh_token  = $r.data.refresh_token
        open_id        = $r.data.open_id
        scope          = $r.data.scope
        expiry_utc     = (Get-Date).AddSeconds($r.data.expires_in).ToString('o')
        token_type     = $r.data.token_type
    }
    $tok | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8

    Write-Host ""
    Write-Host "TikTok auth complete. Token saved to $TokenFile" -ForegroundColor Green
    Write-Host "  Open ID: $($tok.open_id)"
    Write-Host "  Scopes:  $($tok.scope)"
    Write-Log 'Auth' 'OK' "open_id=$($tok.open_id)"
    return $tok
}

# ── actions ──────────────────────────────────────────────────────────────────

function Get-H4YFCreatorInfo {
    Write-Host "Fetching TikTok creator info for @heat4yafeat..." -ForegroundColor Cyan
    $r = Invoke-TT '/post/publish/creator_info/query/'

    Write-Host ""
    Write-Host "Creator Info:" -ForegroundColor Green
    Write-Host "  Creator: $($r.creator_nickname) (@$($r.creator_username))"
    Write-Host "  Avatar:  $($r.creator_avatar_url)"
    Write-Host "  Privacy options available:"
    foreach ($opt in $r.privacy_level_options) {
        Write-Host "    - $opt"
    }
    Write-Host "  Duet disabled:    $($r.duet_disabled)"
    Write-Host "  Stitch disabled:  $($r.stitch_disabled)"
    Write-Host "  Comment disabled: $($r.comment_disabled)"
    Write-Host "  Max video duration: $($r.max_video_post_duration_sec)s"
    Write-Log 'GetCreatorInfo' 'OK' $r.creator_username
    return $r
}

function Get-H4YFVideoList {
    Write-Host "Fetching TikTok video list..." -ForegroundColor Cyan
    $r = Invoke-TT '/video/list/' -body @{
        fields = @('id','title','create_time','view_count','like_count','comment_count','share_count','cover_image_url','duration','embed_link')
        max_count = 20
    }

    Write-Host ""
    Write-Host "Videos ($($r.videos.Count)):" -ForegroundColor Green
    foreach ($v in $r.videos) {
        $date = [DateTimeOffset]::FromUnixTimeSeconds($v.create_time).LocalDateTime.ToString('yyyy-MM-dd')
        Write-Host "  [$($v.id)] $($v.title)"
        Write-Host "    $date | Views: $($v.view_count) | Likes: $($v.like_count) | Comments: $($v.comment_count) | Shares: $($v.share_count)"
    }
    Write-Log 'ListVideos' 'OK' "$($r.videos.Count) videos"
    return $r.videos
}

function Publish-H4YFTikTokVideo {
    param([string]$File, [string]$Cap, [string]$Privacy, [bool]$NoDuet, [bool]$NoStitch, [bool]$NoComment)
    if (-not $File -or -not (Test-Path $File)) { throw "Video file not found: $File" }

    $fileSize = (Get-Item $File).Length
    Write-Host "Initiating TikTok upload ($([Math]::Round($fileSize/1MB,1)) MB)..." -ForegroundColor Cyan

    # Step 1: init upload
    $creatorInfo = Get-H4YFCreatorInfo

    $initBody = @{
        post_info = @{
            title              = if ($Cap) { $Cap } else { '' }
            privacy_level      = if ($Privacy) { $Privacy } else { $PrivacyLevel }
            disable_duet       = if ($NoDuet) { $true } else { $creatorInfo.duet_disabled }
            disable_stitch     = if ($NoStitch) { $true } else { $creatorInfo.stitch_disabled }
            disable_comment    = if ($NoComment) { $true } else { $creatorInfo.comment_disabled }
        }
        source_info = @{
            source      = 'FILE_UPLOAD'
            video_size  = $fileSize
            chunk_size  = 10485760   # 10 MB chunks
            total_chunk_count = [Math]::Ceiling($fileSize / 10485760)
        }
    }

    $init = Invoke-TT '/post/publish/video/init/' -body $initBody
    $publishId = $init.publish_id
    $uploadUrl = $init.upload_url

    Write-Host "Got publish ID: $publishId" -ForegroundColor Cyan
    Write-Host "Uploading in chunks..."

    # Step 2: upload file in chunks
    $token      = Get-AccessToken
    $fileBytes  = [IO.File]::ReadAllBytes($File)
    $chunkSize  = 10485760
    $totalChunks = [Math]::Ceiling($fileSize / $chunkSize)

    for ($i = 0; $i -lt $totalChunks; $i++) {
        $start = $i * $chunkSize
        $end   = [Math]::Min($start + $chunkSize - 1, $fileSize - 1)
        $chunk = $fileBytes[$start..$end]
        $pct   = [Math]::Round((($i + 1) / $totalChunks) * 100)

        Write-Progress -Activity "Uploading to TikTok" -Status "Chunk $($i+1)/$totalChunks ($pct%)" -PercentComplete $pct

        Invoke-RestMethod -Uri $uploadUrl `
            -Method PUT `
            -Headers @{
                'Content-Range' = "bytes $start-$end/$fileSize"
                'Content-Type'  = 'video/mp4'
            } `
            -Body $chunk | Out-Null
    }
    Write-Progress -Activity "Uploading to TikTok" -Completed

    Write-Host "Upload complete. Publish ID: $publishId" -ForegroundColor Green
    Write-Host "Checking publish status..." -ForegroundColor Cyan

    # Step 3: poll status
    $attempts = 0
    do {
        Start-Sleep -Seconds 5
        $status = Invoke-TT '/post/publish/status/fetch/' -body @{ publish_id = $publishId }
        $attempts++
        Write-Host "  Status: $($status.status) ($attempts)" -ForegroundColor Gray
    } while ($status.status -notin @('PUBLISH_COMPLETE','FAILED') -and $attempts -lt 60)

    if ($status.status -eq 'PUBLISH_COMPLETE') {
        Write-Host ""
        Write-Host "Video published successfully!" -ForegroundColor Green
        Write-Host "  Publish ID: $publishId"
        Write-Host "  Status: $($status.status)"
        if ($status.publicaly_available_post_id) {
            Write-Host "  Video ID: $($status.publicaly_available_post_id[0])"
        }
        Write-Log 'PublishVideo' 'OK' "publish_id=$publishId"
    } else {
        Write-Host "Publish failed. Status: $($status.status)" -ForegroundColor Red
        Write-Host ($status | ConvertTo-Json -Depth 5)
        Write-Log 'PublishVideo' 'FAILED' "publish_id=$publishId status=$($status.status)"
        throw "TikTok publish failed: $($status.fail_reason)"
    }
    return $status
}

function Get-H4YFPublishStatus {
    param([string]$PubId)
    if (-not $PubId) { throw "-PublishId is required" }
    Write-Host "Checking status for publish ID: $PubId" -ForegroundColor Cyan
    $r = Invoke-TT '/post/publish/status/fetch/' -body @{ publish_id = $PubId }
    Write-Host "Status: $($r.status)" -ForegroundColor Green
    $r | ConvertTo-Json -Depth 5 | Write-Host
    return $r
}

# ── dispatch ──────────────────────────────────────────────────────────────────

Add-Type -AssemblyName System.Web

switch ($Action) {
    'Auth'                { Invoke-Auth | Out-Null }
    'GetCreatorInfo'      { Get-H4YFCreatorInfo | Out-Null }
    'ListVideos'          { Get-H4YFVideoList | Out-Null }
    'PublishVideo'        {
        Publish-H4YFTikTokVideo `
            -File $VideoFile `
            -Cap $Caption `
            -Privacy $PrivacyLevel `
            -NoDuet $DisableDuet.IsPresent `
            -NoStitch $DisableStitch.IsPresent `
            -NoComment $DisableComment.IsPresent | Out-Null
    }
    'CheckPublishStatus'  { Get-H4YFPublishStatus -PubId $PublishId | Out-Null }
    'GetAnalytics'        {
        Write-Host "TikTok analytics are available via Creator Marketplace (tiktok.com/creator#)" -ForegroundColor Yellow
        Write-Host "Programmatic analytics require the Research API (separate application)." -ForegroundColor Yellow
        Write-Host "For now, use ListVideos to see per-video view/like/comment/share counts." -ForegroundColor Yellow
    }
}
