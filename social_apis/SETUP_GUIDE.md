# H4YF Social API Setup Guide

Scripts: `social_apis/youtube/`, `social_apis/meta/`, `social_apis/tiktok/`
Secrets dir: `C:\Users\JAP\.h4yf_secrets\`

---

## 1. YouTube Data API v3

Uses the **existing GCP project + OAuth client** — no new app needed.

### Steps

**A. Enable YouTube Data API v3 in GCP Console**
1. Go to: https://console.cloud.google.com/apis/library/youtube.googleapis.com?project=1070004533548
2. Click **Enable**
3. Also enable **YouTube Analytics API**: https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com?project=1070004533548

**B. Add YouTube scopes to OAuth consent screen**
1. GCP Console → APIs & Services → OAuth consent screen
2. Under "Scopes" → Add/remove scopes → add:
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
3. Under "Test users" → add `ubiquitousautomation@gmail.com` and Bill's Gmail

**C. Run auth (first time only)**
```powershell
& "C:\Users\JAP\h4yf_youtube_api.ps1" -Action Auth
```
Browser opens → log in as **Bill's YouTube account** → authorize → token saved to `C:\Users\JAP\.h4yf_secrets\youtube_token.json`

**D. Verify**
```powershell
& "C:\Users\JAP\h4yf_youtube_api.ps1" -Action GetChannel
```

**E. Find Campbell's Barbershop video ID to unlist**
```powershell
& "C:\Users\JAP\h4yf_youtube_api.ps1" -Action ListVideos
```

---

## 2. Meta Graph API (Instagram + Facebook)

### Prerequisites
- Instagram @h4yf16 or @heat4yafeat must be an **Instagram Business or Creator** account
- That IG account must be **connected to a Facebook Page** (not a personal profile)
- Bill needs a Facebook Developer account

### Steps

**A. Create Facebook App**
1. Go to: https://developers.facebook.com/apps/create/
2. Select **Business** app type → Continue
3. App name: `H4YF Social` → Create App
4. Note: **App ID** and **App Secret** (Settings → Basic)

**B. Add Products to the App**
- Facebook Login → Set Up
- Instagram Basic Display OR Instagram Graph API → Set Up

**C. Configure Facebook Login**
1. Facebook Login → Settings → Valid OAuth Redirect URIs:
   - Add: `http://localhost:8080/`
2. Permissions to request:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `pages_show_list`
   - `business_management`

**D. Save credentials to secrets file**
Create `C:\Users\JAP\.h4yf_secrets\meta_app_credentials.json`:
```json
{
  "app_id": "YOUR_APP_ID",
  "app_secret": "YOUR_APP_SECRET"
}
```

**E. Run auth**
```powershell
& "C:\Users\JAP\h4yf_meta_api.ps1" -Action Auth
```
Browser opens → log in as **Bill** → authorize → tokens saved to `C:\Users\JAP\.h4yf_secrets\meta_tokens.json`

**F. Verify**
```powershell
& "C:\Users\JAP\h4yf_meta_api.ps1" -Action GetAccounts
```

> **App Review note:** For a **live** Instagram account the `instagram_content_publish` permission requires Meta App Review (takes ~1-3 days). For testing, add Bill as a Test User in the app before review is complete.

---

## 3. TikTok Content Posting API

### Steps

**A. Create TikTok Developer App**
1. Go to: https://developers.tiktok.com/
2. Sign in with the **@heat4yafeat TikTok account** (Josh)
3. Manage Apps → Create App
4. App name: `H4YF` | Category: Content Management
5. Products to add: **Login Kit** + **Content Posting API**
6. Redirect URI: `http://localhost:8080/`
7. Scopes to request: `user.info.basic`, `video.publish`, `video.list`
8. Submit for review → wait for approval (usually 1-3 business days)
9. Note: **Client Key** and **Client Secret**

**B. Save credentials to secrets file**
Create `C:\Users\JAP\.h4yf_secrets\tiktok_app_credentials.json`:
```json
{
  "client_key": "YOUR_CLIENT_KEY",
  "client_secret": "YOUR_CLIENT_SECRET"
}
```

**C. Run auth**
```powershell
& "C:\Users\JAP\h4yf_tiktok_api.ps1" -Action Auth
```
Browser opens → log in as **@heat4yafeat** → authorize → token saved to `C:\Users\JAP\.h4yf_secrets\tiktok_tokens.json`

**D. Verify**
```powershell
& "C:\Users\JAP\h4yf_tiktok_api.ps1" -Action GetCreatorInfo
```

---

## Secrets Directory Reference

```
C:\Users\JAP\.h4yf_secrets\
  gemini_api_key.txt                  # existing — Gemini API
  google_oauth_client_aure.json       # existing — Google OAuth client
  youtube_token.json                  # created by h4yf_youtube_api.ps1 -Action Auth
  meta_app_credentials.json           # MANUAL — create per step 2D above
  meta_tokens.json                    # created by h4yf_meta_api.ps1 -Action Auth
  tiktok_app_credentials.json         # MANUAL — create per step 3B above
  tiktok_tokens.json                  # created by h4yf_tiktok_api.ps1 -Action Auth
```

---

## Quick Action Reference

| Goal | Command |
|---|---|
| Unlist Campbell's Barbershop video | `ListVideos` → copy ID → `Set-Privacy -VideoId X -Privacy unlisted` |
| Upload EP.1 Phantom 6 video | `UploadVideo -VideoFile path -Title "..." -Privacy private` |
| Post TikTok Short | `PublishVideo -VideoFile path -Caption "..."` |
| Post IG Reel | `PublishReel -VideoFile path -Caption "..."` |
| Post to Facebook Page | `PostToPage -Message "..."` |
| Get YouTube analytics | `GetAnalytics -VideoId X` |
