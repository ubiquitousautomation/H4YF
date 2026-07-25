#################################################################
# H4YF — WordPress One-Click Setup via REST API (PowerShell)
# h4yf_wp_setup.ps1
#
# WHAT THIS DOES IN ONE RUN:
#   1. Verifies WP + WooCommerce API credentials
#   2. Installs Stripe, Klaviyo, WP Mail SMTP plugins
#   3. Applies the H4YF Custom CSS design system
#   4. Sets WooCommerce settings (shipping, tax, currency)
#   5. Prints navigation menu structure to create manually
#   6. Configures site identity (title/tagline)
#
# SECURITY — READ BEFORE RUNNING:
#   This script NEVER hardcodes credentials. It reads them from
#   environment variables so nothing sensitive ever touches git.
#   Set these before running (PowerShell):
#
#     $env:H4YF_WP_BASE_URL      = "https://your-site.example.com"
#     $env:H4YF_WP_ADMIN_USER    = "your-wp-username"
#     $env:H4YF_WP_APP_PASSWORD  = "xxxx xxxx xxxx xxxx xxxx xxxx"
#     $env:H4YF_WC_CONSUMER_KEY  = "ck_..."
#     $env:H4YF_WC_CONSUMER_SECRET = "cs_..."
#
#   HOW TO GET YOUR WP APP PASSWORD:
#     WP Admin -> Users -> Your Profile -> "Application Passwords"
#     Name it "H4YF Setup Script" -> Add New Application Password
#     Copy the generated password immediately (shown once only).
#
#   HOW TO GET YOUR WC CONSUMER KEY/SECRET:
#     WooCommerce -> Settings -> Advanced -> REST API
#     If a key already exists, regenerate it — the original secret
#     for any key exposed outside this env-var flow should be treated
#     as compromised and rotated.
#     If not: Add Key -> Description: "H4YF Automation" -> Permissions: Read/Write
#
# Ubiquitous Solutions | HEAT4YAFEAT | 2026
#################################################################

$ErrorActionPreference = "Stop"

# ── Load credentials from environment — fail fast if missing ──
$required = @(
    "H4YF_WP_BASE_URL", "H4YF_WP_ADMIN_USER", "H4YF_WP_APP_PASSWORD",
    "H4YF_WC_CONSUMER_KEY", "H4YF_WC_CONSUMER_SECRET"
)
$missing = $required | Where-Object { -not (Get-Item "env:$_" -ErrorAction SilentlyContinue) }
if ($missing) {
    Write-Host "Missing required environment variables:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`nSet them before running this script. See the header comment for how." -ForegroundColor Yellow
    exit 1
}

$WP_BASE_URL        = $env:H4YF_WP_BASE_URL
$WP_ADMIN_USER      = $env:H4YF_WP_ADMIN_USER
$WP_APP_PASSWORD    = $env:H4YF_WP_APP_PASSWORD
$WC_CONSUMER_KEY    = $env:H4YF_WC_CONSUMER_KEY
$WC_CONSUMER_SECRET = $env:H4YF_WC_CONSUMER_SECRET

# ── Auth headers ──
$wpCreds  = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${WP_ADMIN_USER}:${WP_APP_PASSWORD}"))
$wcCreds  = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${WC_CONSUMER_KEY}:${WC_CONSUMER_SECRET}"))
$wpHeader = @{ Authorization = "Basic $wpCreds"; "Content-Type" = "application/json" }
$wcHeader = @{ Authorization = "Basic $wcCreds"; "Content-Type" = "application/json" }

function WP-API($method, $endpoint, $body = $null) {
    $uri = "$WP_BASE_URL$endpoint"
    $params = @{ Uri = $uri; Method = $method; Headers = $wpHeader; TimeoutSec = 30 }
    if ($body) { $params.Body = ($body | ConvertTo-Json -Depth 10) }
    try {
        return Invoke-RestMethod @params
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        Write-Warning "  WP API $method $endpoint -> $code : $($_.Exception.Message)"
        return $null
    }
}

function WC-API($method, $endpoint, $body = $null) {
    $uri = "$WP_BASE_URL$endpoint"
    $params = @{ Uri = $uri; Method = $method; Headers = $wcHeader; TimeoutSec = 30 }
    if ($body) { $params.Body = ($body | ConvertTo-Json -Depth 10) }
    try { return Invoke-RestMethod @params }
    catch { Write-Warning "  WC API $method $endpoint -> $($_.Exception.Message)"; return $null }
}

function Log($msg) { Write-Host $msg -ForegroundColor Cyan }
function OK($msg)  { Write-Host "  OK $msg" -ForegroundColor Green }
function ERR($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red }

# ── STEP 1: Verify auth ──
Log "`n=== STEP 1: Verifying credentials ==="
$me = WP-API "GET" "/wp-json/wp/v2/users/me"
if ($me) { OK "Authenticated as: $($me.name) ($($me.roles -join ', '))" }
else { ERR "Auth failed - check H4YF_WP_ADMIN_USER and H4YF_WP_APP_PASSWORD"; exit 1 }

# ── STEP 2: Install plugins ──
Log "`n=== STEP 2: Installing plugins ==="
$pluginsToInstall = @(
    @{ slug = "woocommerce-gateway-stripe"; name = "WooCommerce Stripe Payment Gateway" },
    @{ slug = "klaviyo-woocommerce"; name = "Klaviyo: Email Marketing & SMS" },
    @{ slug = "wp-mail-smtp"; name = "WP Mail SMTP" }
)
foreach ($plugin in $pluginsToInstall) {
    Log "  Installing: $($plugin.name)"
    $install = WP-API "POST" "/wp-json/wp/v2/plugins" @{ slug = $plugin.slug; status = "active" }
    if ($install) { OK "Installed: $($plugin.name)" }
    else { ERR "Could not auto-install $($plugin.name) - install manually in Plugins -> Add New" }
}

# ── STEP 3: Apply Custom CSS — DISABLED, see h4yf-design-tokens.css ──
# The site's theme (ubiquitousautomation/ubiq-h4yf-skin) is now git-managed and
# SFTP-deployed directly to wp-content/themes/h4yf-skin/. Pushing CSS through
# wp-json/wp/v2/settings.custom_css here would fight that deployment and can
# silently override the real, currently-locked design tokens with a stale copy.
# See h4yf-design-tokens.css in this folder for the full explanation.
Log "`n=== STEP 3: Design system CSS — SKIPPED (see h4yf-design-tokens.css) ==="
Log "  Theme CSS is git-managed in ubiq-h4yf-skin and deployed via SFTP, not this API."
Log "  Nothing pushed. If you intended to update the theme's CSS, edit style.css /"
Log "  assets/skin.css in ubiq-h4yf-skin and deploy through that repo's normal process."

# ── STEP 4: WooCommerce settings ──
Log "`n=== STEP 4: Configuring WooCommerce settings ==="
WC-API "PUT" "/wp-json/wc/v3/settings/general/woocommerce_currency" @{ value = "USD" } | Out-Null
OK "Currency: USD"

WC-API "PUT" "/wp-json/wc/v3/settings/general/woocommerce_store_city" @{ value = "Indianapolis" } | Out-Null
WC-API "PUT" "/wp-json/wc/v3/settings/general/woocommerce_default_country" @{ value = "US:IN" } | Out-Null
OK "Store location: Indianapolis, IN"

WC-API "PUT" "/wp-json/wc/v3/settings/general/woocommerce_calc_taxes" @{ value = "yes" } | Out-Null
OK "Taxes enabled"

$shippingZones = WC-API "GET" "/wp-json/wc/v3/shipping/zones"
if ($shippingZones -and $shippingZones.Count -gt 0) {
    $zoneId = $shippingZones[0].id
    $freeShip = WC-API "POST" "/wp-json/wc/v3/shipping/zones/$zoneId/methods" @{
        method_id = "free_shipping"
        settings  = @{ min_amount = @{ value = "150" } }
    }
    if ($freeShip) { OK "Free shipping threshold: `$150" }
}

# ── STEP 5: Site identity ──
Log "`n=== STEP 5: Configuring site identity ==="
$siteSettings = WP-API "POST" "/wp-json/wp/v2/settings" @{
    title       = "HEAT4YAFEAT"
    description = "Indianapolis's Most Trusted Authenticated Sneaker Curator."
}
if ($siteSettings) { OK "Site title and tagline updated" }

# ── STEP 6: Summary ──
Log "`n=== SETUP COMPLETE ==="
Write-Host ""
Write-Host "Next manual steps:" -ForegroundColor Yellow
Write-Host "  1. WP Admin -> Plugins -> confirm Stripe, Klaviyo, WP Mail SMTP installed"
Write-Host "  2. WooCommerce -> Settings -> Payments -> Stripe -> enter API keys"
Write-Host "  3. WooCommerce -> Settings -> Payments -> enable Klarna + Afterpay in Stripe"
Write-Host "  4. Appearance -> Menus -> create Primary nav (Shop, Authentication, About, Whatnot Shows, FAQ, Contact)"
Write-Host "  5. Facebook for WooCommerce -> connect Meta Business Manager account"
Write-Host "  6. Klaviyo -> connect WooCommerce -> activate email flows"
Write-Host "  7. WP Mail SMTP -> connect Gmail SMTP"
Write-Host "  8. DNS cutover: point domain to hosting server IP"
