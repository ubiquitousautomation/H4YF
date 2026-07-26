/**
 * h4yf_ebay_image_fetcher.gs
 * Pulls product images from eBay via the official Browse API and attaches them
 * to matching WooCommerce products. Legitimate API access — no scraping.
 *
 * WHY: eBay/StockX block scraping (403 / PerimeterX). The eBay CSV export has
 * Item IDs but no image URLs. The Browse API returns image URLs by Item ID.
 *
 * SOURCE OF ITEM IDs: eBay active-listings CSV export
 *   Drive file: set via Script Property H4YF_EBAY_CSV_FILE_ID (columns: "Item number","Title",...)
 * MATCH TO: WooCommerce products, matched by normalized Title <-> product Name
 *           (eBay export SKUs are mostly blank, so we match on title.)
 *
 * ============ ONE-TIME eBay SETUP (user) ============
 *  1. Go to developer.ebay.com -> sign in with the eBay account -> "Create an app key set"
 *  2. Choose PRODUCTION keys. Copy:
 *        App ID  (Client ID)
 *        Cert ID (Client Secret)
 *  3. Set both as Script Properties (see below).
 *  No redirect URL / user token needed — Browse API uses client_credentials (app token).
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
 *     H4YF_EBAY_CLIENT_ID      = <production App ID>
 *     H4YF_EBAY_CLIENT_SECRET  = <production Cert ID>
 *     H4YF_EBAY_CSV_FILE_ID    = <Drive file ID of the eBay active-listings CSV export>
 *     H4YF_WP_BASE_URL         = https://your-site.example.com
 *     H4YF_WP_USER             = your-wp-username-or-email
 *     H4YF_WP_APP_PASS         = xxxx xxxx xxxx xxxx xxxx xxxx
 *
 * ============ HOW TO RUN ============
 *  1. Paste this whole file into a new Apps Script project (script.google.com)
 *  2. Run testEbayAuth()       -> confirms your keys mint an OAuth token
 *  3. Run testOneItem()        -> fetches images for a single known Item ID (sanity check;
 *                                 set H4YF_EBAY_TEST_ITEM_ID as a Script Property)
 *  4. Run previewImageMatch()  -> logs eBay-listing -> WC-product matches, NO writes
 *  5. Review the match log. If matches look right, run executeImagePush()
 *
 * SAFE: only executeImagePush() writes, and it only sets the product images array.
 *       It never changes price, stock, title, or SEO meta.
 */

function getConfig_() {
  const props = PropertiesService.getScriptProperties();
  const cfg = {
    EBAY_CLIENT_ID: props.getProperty('H4YF_EBAY_CLIENT_ID'),
    EBAY_CLIENT_SECRET: props.getProperty('H4YF_EBAY_CLIENT_SECRET'),
    EBAY_CSV_FILE_ID: props.getProperty('H4YF_EBAY_CSV_FILE_ID'),
    WP_BASE_URL: props.getProperty('H4YF_WP_BASE_URL'),
    WP_USER: props.getProperty('H4YF_WP_USER'),
    WP_APP_PASS: props.getProperty('H4YF_WP_APP_PASS'),
    TEST_ITEM_ID: props.getProperty('H4YF_EBAY_TEST_ITEM_ID'),
  };
  const required = ['EBAY_CLIENT_ID', 'EBAY_CLIENT_SECRET', 'EBAY_CSV_FILE_ID', 'WP_BASE_URL', 'WP_USER', 'WP_APP_PASS'];
  const missing = required.filter((k) => !cfg[k]);
  if (missing.length) {
    throw new Error(
      'Missing Script Properties: ' + missing.join(', ') +
      '. Set them under Project Settings -> Script Properties before running.'
    );
  }
  return cfg;
}

const EBAY_MARKETPLACE = 'EBAY_US';
const EBAY_COL_ITEMID = 'Item number';
const EBAY_COL_TITLE = 'Title';
const MATCH_THRESHOLD = 0.55; // token-overlap score required to accept a fuzzy match

// ============ eBay OAuth (client credentials) ============
function _ebayToken_() {
  const cfg = getConfig_();
  const creds = Utilities.base64Encode(cfg.EBAY_CLIENT_ID + ':' + cfg.EBAY_CLIENT_SECRET);
  const resp = UrlFetchApp.fetch('https://api.ebay.com/identity/v1/oauth2/token', {
    method: 'post',
    headers: { Authorization: 'Basic ' + creds },
    contentType: 'application/x-www-form-urlencoded',
    payload: { grant_type: 'client_credentials', scope: 'https://api.ebay.com/oauth/api_scope' },
    muteHttpExceptions: true,
  });
  if (resp.getResponseCode() !== 200) throw new Error('eBay auth failed: ' + resp.getContentText());
  return JSON.parse(resp.getContentText()).access_token;
}

function testEbayAuth() {
  const t = _ebayToken_();
  Logger.log('OK - token length ' + t.length + ' (auth working)');
}

// ============ FETCH IMAGES FOR ONE ITEM ============
function _itemImages_(token, legacyId) {
  const url = 'https://api.ebay.com/buy/browse/v1/item/get_item_by_legacy_id?legacy_item_id=' + legacyId;
  const resp = UrlFetchApp.fetch(url, {
    headers: {
      Authorization: 'Bearer ' + token,
      'X-EBAY-C-MARKETPLACE-ID': EBAY_MARKETPLACE,
    },
    muteHttpExceptions: true,
  });
  if (resp.getResponseCode() !== 200) return null;
  const item = JSON.parse(resp.getContentText());
  const imgs = [];
  if (item.image && item.image.imageUrl) imgs.push(item.image.imageUrl);
  if (item.additionalImages) item.additionalImages.forEach((a) => { if (a.imageUrl) imgs.push(a.imageUrl); });
  return imgs;
}

function testOneItem() {
  const cfg = getConfig_();
  if (!cfg.TEST_ITEM_ID) throw new Error('Set H4YF_EBAY_TEST_ITEM_ID as a Script Property first.');
  const token = _ebayToken_();
  const imgs = _itemImages_(token, cfg.TEST_ITEM_ID);
  Logger.log('Item ' + cfg.TEST_ITEM_ID + ' -> ' + (imgs ? imgs.length + ' images' : 'NOT FOUND'));
  if (imgs) imgs.forEach((u) => { Logger.log('  ' + u); });
}

// ============ NORMALIZE TITLE FOR MATCHING ============
function _norm_(s) {
  return String(s)
    .replace(/heat4yafeat presents/ig, ' ')
    .replace(/[^a-z0-9 ]/ig, ' ')          // strip emojis, quotes, punctuation
    .replace(/\b(sz|size)\s*\d+(\.\d+)?\b/ig, ' ') // strip size tokens
    .replace(/\bauthentic(ated)?\b/ig, ' ')
    .replace(/\bmens?\b/ig, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}
function _score_(a, b) {
  const ta = _norm_(a).split(' ').filter(Boolean);
  const tb = _norm_(b).split(' ').filter(Boolean);
  if (!ta.length || !tb.length) return 0;
  const setB = {}; tb.forEach((t) => { setB[t] = 1; });
  let hit = 0; ta.forEach((t) => { if (setB[t]) hit++; });
  return hit / Math.max(ta.length, tb.length);
}

// ============ READ eBay CSV ============
function _readEbayCsv_() {
  const cfg = getConfig_();
  const csv = DriveApp.getFileById(cfg.EBAY_CSV_FILE_ID).getBlob().getDataAsString('UTF-8');
  const rows = Utilities.parseCsv(csv);
  const head = rows[0].map((h) => String(h).replace(/^﻿/, '').trim());
  const iId = head.indexOf(EBAY_COL_ITEMID), iT = head.indexOf(EBAY_COL_TITLE);
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    const id = String(rows[i][iId]).trim();
    const t = String(rows[i][iT]).trim();
    if (id && t) out.push({ itemId: id, title: t });
  }
  return out;
}

// ============ READ WC PRODUCTS (id, name, sku, hasImage) ============
function _readWcProducts_() {
  const cfg = getConfig_();
  const out = [];
  let page = 1;
  const headers = { Authorization: 'Basic ' + Utilities.base64Encode(cfg.WP_USER + ':' + cfg.WP_APP_PASS) };
  while (true) {
    const url = cfg.WP_BASE_URL + '/wp-json/wc/v3/products?per_page=100&page=' + page + '&_fields=id,name,sku,images';
    const resp = UrlFetchApp.fetch(url, { headers: headers, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) break;
    const batch = JSON.parse(resp.getContentText());
    if (!batch.length) break;
    batch.forEach((p) => { out.push({ id: p.id, name: p.name, sku: p.sku, hasImage: (p.images && p.images.length > 0) }); });
    if (batch.length < 100) break;
    page++;
  }
  return out;
}

// ============ MATCH eBay listing -> WC product ============
function _matchAll_() {
  const ebay = _readEbayCsv_();
  const wc = _readWcProducts_();
  const matches = [];
  ebay.forEach((e) => {
    let best = null, bestScore = 0;
    wc.forEach((p) => {
      const sc = _score_(e.title, p.name);
      if (sc > bestScore) { bestScore = sc; best = p; }
    });
    if (best && bestScore >= MATCH_THRESHOLD) {
      matches.push({ itemId: e.itemId, ebayTitle: e.title, wcId: best.id, wcName: best.name, score: bestScore.toFixed(2), hasImage: best.hasImage });
    } else {
      matches.push({ itemId: e.itemId, ebayTitle: e.title, wcId: null, wcName: '(no match)', score: bestScore.toFixed(2), hasImage: false });
    }
  });
  return matches;
}

// ============ PREVIEW (DRY RUN) ============
function previewImageMatch() {
  const m = _matchAll_();
  const matched = m.filter((x) => x.wcId);
  Logger.log('eBay listings: ' + m.length + ' | matched to WC: ' + matched.length + ' | unmatched: ' + (m.length - matched.length));
  Logger.log('--- first 25 matches ---');
  matched.slice(0, 25).forEach((x) => {
    Logger.log('[' + x.score + '] ' + x.itemId + ' "' + x.ebayTitle + '"  ->  #' + x.wcId + ' "' + x.wcName + '"' + (x.hasImage ? ' (already has image)' : ''));
  });
  Logger.log('--- unmatched (need StockX/shoot) ---');
  m.filter((x) => !x.wcId).slice(0, 25).forEach((x) => { Logger.log('  ' + x.itemId + ' "' + x.ebayTitle + '" (best ' + x.score + ')'); });
}

// ============ EXECUTE (WRITES IMAGES) ============
function executeImagePush() {
  const cfg = getConfig_();
  const token = _ebayToken_();
  const m = _matchAll_().filter((x) => x.wcId && !x.hasImage);
  const wpHeaders = { Authorization: 'Basic ' + Utilities.base64Encode(cfg.WP_USER + ':' + cfg.WP_APP_PASS), 'Content-Type': 'application/json' };
  let done = 0, noImg = 0, failed = 0;

  m.forEach((x) => {
    const imgs = _itemImages_(token, x.itemId);
    if (!imgs || !imgs.length) { noImg++; return; }
    const payload = { images: imgs.slice(0, 8).map((u) => ({ src: u })) }; // cap at 8 imgs/product
    const resp = UrlFetchApp.fetch(cfg.WP_BASE_URL + '/wp-json/wc/v3/products/' + x.wcId, {
      method: 'put', headers: wpHeaders, payload: JSON.stringify(payload), muteHttpExceptions: true,
    });
    if (resp.getResponseCode() === 200) { done++; } else { failed++; Logger.log('FAIL #' + x.wcId + ': ' + resp.getResponseCode()); }
    Utilities.sleep(400); // WordPress sideloads each image server-side — give it room
  });

  Logger.log('=== IMAGE PUSH COMPLETE ===');
  Logger.log('Products imaged: ' + done + ' | eBay had no image: ' + noImg + ' | failed: ' + failed);
  Logger.log('Remaining imageless products = source from StockX (style code) or in-house shoot.');
}
