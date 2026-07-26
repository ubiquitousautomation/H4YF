/**
 * h4yf_seo_pusher.gs
 * Programmatically pushes SEO / LLM / Schema meta from the SEO source sheet
 * to live WooCommerce products, matched by SKU.
 *
 * SOURCE: "h4yf — 03 SEO · AEO · Content", tab "Listing SEO Manager"
 * TARGET: WooCommerce products on the WP site (RankMath post meta)
 *
 * Pushes per product:
 *   - rank_math_title          (Meta Title — Website column)
 *   - rank_math_description    (Meta Description 160 char column)
 *   - rank_math_focus_keyword  (Primary Keyword column)
 *   - _h4yf_ai_description     (AI Description first-150-char LLM citation zone)
 *   - _h4yf_schema_type        (Schema Type)
 *
 * SECURITY — READ BEFORE RUNNING:
 * Credentials come from Apps Script's PropertiesService, never hardcoded.
 * The original Drive copy of this script had a live WordPress username
 * (a real email address) and a live Application Password hardcoded — both
 * were removed. If that Application Password is still active, revoke it:
 * WP Admin -> Users -> Your Profile -> Application Passwords -> Revoke.
 *
 * Set these once per Apps Script project:
 *   Extensions -> Apps Script -> Project Settings -> Script Properties
 *     H4YF_SEO_SHEET_ID   = <Google Sheet ID>
 *     H4YF_WP_BASE_URL    = https://your-site.example.com
 *     H4YF_WP_USER        = your-wp-username-or-email
 *     H4YF_WP_APP_PASS    = xxxx xxxx xxxx xxxx xxxx xxxx
 *
 * HOW TO RUN:
 *   1. Paste into a new Apps Script project at script.google.com
 *   2. Run previewSEOPush()  -> logs first 10 matches, NO writes (dry run)
 *   3. Review the log. If matches look right, run executeSEOPush()
 *   4. executeSEOPush() processes all rows, logs a summary + any unmatched SKUs
 *
 * SAFE: previewSEOPush() never writes. executeSEOPush() only updates meta —
 * it never touches price, stock, title, or images.
 */

function getConfig_() {
  const props = PropertiesService.getScriptProperties();
  const cfg = {
    SEO_SHEET_ID: props.getProperty('H4YF_SEO_SHEET_ID'),
    WP_BASE_URL: props.getProperty('H4YF_WP_BASE_URL'),
    WP_USER: props.getProperty('H4YF_WP_USER'),
    WP_APP_PASS: props.getProperty('H4YF_WP_APP_PASS'),
  };
  const missing = Object.entries(cfg).filter(([, v]) => !v).map(([k]) => k);
  if (missing.length) {
    throw new Error(
      'Missing Script Properties: ' + missing.join(', ') +
      '. Set them under Project Settings -> Script Properties before running.'
    );
  }
  return cfg;
}

const SEO_TAB_NAME = 'Listing SEO Manager';

// Column headers in the SEO sheet (match exactly; trims applied)
const COL = {
  sku: 'SKU',
  metaTitle: 'Meta Title (Website)',
  metaDesc: 'Meta Description (160 chars)',
  focusKw: 'Primary Keyword',
  aiDesc: 'AI Description (First 150 chars)',
  schemaType: 'Schema Type',
};

// ============ AUTH ============
function _authHeader_() {
  const cfg = getConfig_();
  const raw = cfg.WP_USER + ':' + cfg.WP_APP_PASS;
  return 'Basic ' + Utilities.base64Encode(raw);
}

// ============ READ SEO SHEET ============
function _readSeoRows_() {
  const cfg = getConfig_();
  const sh = SpreadsheetApp.openById(cfg.SEO_SHEET_ID).getSheetByName(SEO_TAB_NAME);
  if (!sh) throw new Error('Tab not found: ' + SEO_TAB_NAME);
  const values = sh.getDataRange().getValues();

  // Find the header row (the one containing "SKU")
  let headerRow = -1, headers = [];
  for (let r = 0; r < Math.min(values.length, 10); r++) {
    const row = values[r].map((c) => String(c).trim());
    if (row.indexOf(COL.sku) !== -1) { headerRow = r; headers = row; break; }
  }
  if (headerRow === -1) throw new Error('Could not locate header row with "SKU"');

  const idx = {};
  Object.keys(COL).forEach((k) => { idx[k] = headers.indexOf(COL[k]); });
  if (idx.sku === -1) throw new Error('SKU column not found');

  const rows = [];
  for (let i = headerRow + 1; i < values.length; i++) {
    const v = values[i];
    const sku = String(v[idx.sku]).trim();
    if (!sku || sku.toUpperCase().indexOf('H4YF') !== 0) continue;
    rows.push({
      sku: sku,
      metaTitle: idx.metaTitle > -1 ? String(v[idx.metaTitle]).trim() : '',
      metaDesc: idx.metaDesc > -1 ? String(v[idx.metaDesc]).trim() : '',
      focusKw: idx.focusKw > -1 ? String(v[idx.focusKw]).trim() : '',
      aiDesc: idx.aiDesc > -1 ? String(v[idx.aiDesc]).trim() : '',
      schemaType: idx.schemaType > -1 ? String(v[idx.schemaType]).trim() : '',
    });
  }
  return rows;
}

// ============ BUILD SKU -> WC PRODUCT ID MAP ============
function _buildSkuMap_() {
  const cfg = getConfig_();
  const map = {};
  let page = 1;
  const headers = { Authorization: _authHeader_() };
  while (true) {
    const url = cfg.WP_BASE_URL + '/wp-json/wc/v3/products?per_page=100&page=' + page + '&_fields=id,sku';
    const resp = UrlFetchApp.fetch(url, { headers: headers, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) break;
    const batch = JSON.parse(resp.getContentText());
    if (!batch.length) break;
    batch.forEach((p) => { if (p.sku) map[p.sku.trim()] = p.id; });
    if (batch.length < 100) break;
    page++;
  }
  return map;
}

// ============ PREVIEW (DRY RUN) ============
function previewSEOPush() {
  const rows = _readSeoRows_();
  const skuMap = _buildSkuMap_();
  Logger.log('SEO rows: ' + rows.length + ' | WC products with SKU: ' + Object.keys(skuMap).length);
  let matched = 0, shown = 0;
  rows.forEach((row) => {
    const pid = skuMap[row.sku];
    if (pid) {
      matched++;
      if (shown < 10) {
        shown++;
        Logger.log('--- ' + row.sku + ' -> product ' + pid + ' ---');
        Logger.log('  title: ' + row.metaTitle);
        Logger.log('  desc:  ' + row.metaDesc);
        Logger.log('  kw:    ' + row.focusKw);
      }
    }
  });
  Logger.log('MATCHED ' + matched + ' / ' + rows.length + ' rows. (No writes performed.)');
}

// ============ EXECUTE (WRITES) ============
function executeSEOPush() {
  const cfg = getConfig_();
  const rows = _readSeoRows_();
  const skuMap = _buildSkuMap_();
  let updated = 0, skipped = 0, failed = 0;
  const unmatched = [];

  rows.forEach((row) => {
    const pid = skuMap[row.sku];
    if (!pid) { unmatched.push(row.sku); skipped++; return; }

    const meta = [];
    if (row.metaTitle) meta.push({ key: 'rank_math_title', value: row.metaTitle });
    if (row.metaDesc) meta.push({ key: 'rank_math_description', value: row.metaDesc });
    if (row.focusKw) meta.push({ key: 'rank_math_focus_keyword', value: row.focusKw });
    if (row.aiDesc) meta.push({ key: '_h4yf_ai_description', value: row.aiDesc });
    if (row.schemaType) meta.push({ key: '_h4yf_schema_type', value: row.schemaType });
    if (!meta.length) { skipped++; return; }

    const url = cfg.WP_BASE_URL + '/wp-json/wc/v3/products/' + pid;
    const opts = {
      method: 'put',
      contentType: 'application/json',
      headers: { Authorization: _authHeader_() },
      payload: JSON.stringify({ meta_data: meta }),
      muteHttpExceptions: true,
    };
    const resp = UrlFetchApp.fetch(url, opts);
    if (resp.getResponseCode() === 200) { updated++; }
    else { failed++; Logger.log('FAIL ' + row.sku + ' (' + pid + '): ' + resp.getResponseCode()); }
    Utilities.sleep(120); // gentle rate limit
  });

  Logger.log('=== SEO PUSH COMPLETE ===');
  Logger.log('Updated: ' + updated + ' | Skipped(no data/no match): ' + skipped + ' | Failed: ' + failed);
  if (unmatched.length) Logger.log('Unmatched SKUs (' + unmatched.length + '): ' + unmatched.join(', '));
}
