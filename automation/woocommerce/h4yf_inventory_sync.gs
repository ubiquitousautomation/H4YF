/**
 * H4YF — Inventory Sync & Automation Engine
 * h4yf_inventory_sync.gs
 *
 * PURPOSE: Bidirectional sync between the Master Catalog (Google Sheets)
 * and all active sales channels (WooCommerce, eBay delist flags, sale
 * tracking).
 *
 * SETUP: Paste this entire file into script.google.com as a new
 * standalone project named "h4yf_inventory_sync". Then run
 * setupTriggers() once to install all time-based triggers. Do NOT run
 * sync functions manually after triggers are set — they fire
 * automatically.
 *
 * SECURITY — READ BEFORE RUNNING:
 * Credentials come from Apps Script's PropertiesService, never hardcoded.
 * The original Drive copy of this script had a live-looking WooCommerce
 * REST API consumer key hardcoded in CONFIG.WC_CONSUMER_KEY — that value
 * was NOT carried into this repo. If that key is still active, rotate
 * it (WooCommerce -> Settings -> Advanced -> REST API -> regenerate).
 *
 * Set these once per Apps Script project:
 *   Extensions -> Apps Script -> Project Settings -> Script Properties
 *     H4YF_WC_BASE_URL         = https://your-site.example.com
 *     H4YF_WC_CONSUMER_KEY     = ck_...
 *     H4YF_WC_CONSUMER_SECRET  = cs_...
 *     H4YF_WP_ADMIN_USER       = your-wp-username
 *     H4YF_WP_APP_PASSWORD     = xxxx xxxx xxxx xxxx xxxx xxxx
 *     H4YF_MASTER_CATALOG_ID   = <Google Sheet ID>
 *     H4YF_SALES_TRACKER_ID    = <Google Sheet ID>
 *
 * Sheet IDs are not secrets in the same sense as API keys, but they're
 * also environment-specific — kept out of source for the same reason:
 * this script should work unmodified across environments (staging/prod)
 * by only changing Script Properties.
 *
 * Ubiquitous Solutions | HEAT4YAFEAT | 2026
 */

function getConfig_() {
  const props = PropertiesService.getScriptProperties();
  const cfg = {
    MASTER_CATALOG_ID: props.getProperty('H4YF_MASTER_CATALOG_ID'),
    SALES_TRACKER_ID: props.getProperty('H4YF_SALES_TRACKER_ID'),
    WC_BASE_URL: props.getProperty('H4YF_WC_BASE_URL'),
    WC_CONSUMER_KEY: props.getProperty('H4YF_WC_CONSUMER_KEY'),
    WC_CONSUMER_SECRET: props.getProperty('H4YF_WC_CONSUMER_SECRET'),
    WP_ADMIN_USER: props.getProperty('H4YF_WP_ADMIN_USER'),
    WP_APP_PASSWORD: props.getProperty('H4YF_WP_APP_PASSWORD'),
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

// Sheet tab names
const CATALOG_TAB = 'H4YF Full Catalog';
const LIVE_INV_TAB = 'Live Inventory';
const SALES_TAB = 'Sales Tracker';

// Column indices in Master Catalog (0-based)
const COL = {
  SKU: 0,
  BRAND: 1,
  MODEL: 2,
  COLORWAY: 3,
  SIZE: 4,
  CONDITION: 5,
  COST: 6,
  PRICE: 7,
  WC_ID: 8,               // WooCommerce Product ID
  EBAY_ID: 9,             // eBay Item ID
  STOCKX_ID: 10,          // StockX listing ID
  STATUS_SITE: 11,        // Platform Status - Website
  STATUS_EBAY: 12,        // Platform Status - eBay
  STATUS_STOCKX: 13,      // Platform Status - StockX
  IMAGE_URL: 14,          // Google Drive image URL (publicly shared)
  GTIN: 15,               // UPC/GTIN
  DESCRIPTION: 16,        // Product description
  CATEGORY: 17,           // WC category name
  TAGS: 18,               // Comma-separated tags
  SYNC_STATUS: 19,        // Sync Status: Pending / Synced / Error / Sold
  SYNC_TIMESTAMP: 20,     // Last synced timestamp
};

// ── TRIGGER SETUP — run once ──────────────────────────────────────

function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));

  // Sync pending items to WooCommerce every 2 hours
  ScriptApp.newTrigger('syncPendingToWooCommerce')
    .timeBased().everyHours(2).create();

  // Full status audit every morning at 7 AM
  ScriptApp.newTrigger('dailyStatusAudit')
    .timeBased().atHour(7).everyDays(1).create();

  // Weekly sales report every Monday at 8 AM
  ScriptApp.newTrigger('weeklyReport')
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(8).create();

  Logger.log('All triggers installed. Sync runs every 2 hours automatically.');
}

// ── CORE SYNC: PENDING -> WOOCOMMERCE ─────────────────────────────

function syncPendingToWooCommerce() {
  const cfg = getConfig_();
  const sheet = SpreadsheetApp.openById(cfg.MASTER_CATALOG_ID).getSheetByName(CATALOG_TAB);
  const data = sheet.getDataRange().getValues();

  let synced = 0, errors = 0;

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const syncStatus = row[COL.SYNC_STATUS];
    const wcId = row[COL.WC_ID];

    if (syncStatus !== 'Pending') continue;

    try {
      const product = buildWcProductPayload(row);

      if (wcId && wcId !== '') {
        wcApiRequest('PUT', `/wp-json/wc/v3/products/${wcId}`, product);
        Logger.log(`Updated WC product ${wcId} - SKU: ${row[COL.SKU]}`);
      } else {
        const result = wcApiRequest('POST', '/wp-json/wc/v3/products', product);
        sheet.getRange(i + 1, COL.WC_ID + 1).setValue(result.id);
        Logger.log(`Created WC product ${result.id} - SKU: ${row[COL.SKU]}`);
      }

      sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Synced');
      sheet.getRange(i + 1, COL.SYNC_TIMESTAMP + 1).setValue(new Date().toISOString());
      synced++;
    } catch (e) {
      sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Error: ' + e.message);
      errors++;
      Logger.log(`Error on row ${i + 1}: ${e.message}`);
    }

    Utilities.sleep(300); // respect WC API rate limits
  }

  Logger.log(`Sync complete. Synced: ${synced} | Errors: ${errors}`);
}

// ── MARK ITEM SOLD — call this when a sale is recorded ────────────

/**
 * Call this function when a sale is confirmed on any platform. It marks
 * the item sold in the catalog, sets WC to out-of-stock, and logs the
 * sale to the Sales Tracker.
 *
 * @param {string} sku - The H4YF SKU (e.g. "H4YF-001")
 * @param {string} platform - Where it sold: "website" | "ebay" | "stockx" | "whatnot" | "grailed"
 * @param {number} salePrice - Actual sale price
 * @param {string} orderId - Platform order/transaction ID
 */
function markItemSold(sku, platform, salePrice, orderId) {
  const cfg = getConfig_();
  const sheet = SpreadsheetApp.openById(cfg.MASTER_CATALOG_ID).getSheetByName(CATALOG_TAB);
  const data = sheet.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    if (data[i][COL.SKU] !== sku) continue;

    const wcId = data[i][COL.WC_ID];
    const costBasis = data[i][COL.COST];

    sheet.getRange(i + 1, COL.STATUS_SITE + 1).setValue('SOLD');
    sheet.getRange(i + 1, COL.STATUS_EBAY + 1).setValue('SOLD');
    sheet.getRange(i + 1, COL.STATUS_STOCKX + 1).setValue('SOLD');
    sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Sold');

    if (wcId) {
      try {
        wcApiRequest('PUT', `/wp-json/wc/v3/products/${wcId}`, {
          stock_status: 'outofstock',
          status: 'private', // hide from shop
        });
        Logger.log(`WC product ${wcId} set to out of stock`);
      } catch (e) {
        Logger.log(`Warning: Could not update WC product ${wcId}: ${e.message}`);
      }
    }

    logSaleToTracker(sku, platform, salePrice, costBasis, orderId,
      data[i][COL.BRAND], data[i][COL.MODEL],
      data[i][COL.COLORWAY], data[i][COL.SIZE]);

    Logger.log(`SKU ${sku} marked SOLD on ${platform} for $${salePrice}`);
    return;
  }

  Logger.log(`SKU ${sku} not found in Master Catalog`);
}

function logSaleToTracker(sku, platform, salePrice, cost, orderId, brand, model, colorway, size) {
  const cfg = getConfig_();
  const ss = SpreadsheetApp.openById(cfg.SALES_TRACKER_ID);
  const sheet = ss.getSheetByName(SALES_TAB) || ss.getSheets()[0];

  const margin = salePrice - cost;
  const marginPct = cost > 0 ? ((margin / cost) * 100).toFixed(1) : 'N/A';

  sheet.appendRow([
    new Date(),      // Date
    sku,             // SKU
    brand,           // Brand
    model,           // Model
    colorway,        // Colorway
    size,            // Size
    platform,        // Platform
    salePrice,       // Sale Price
    cost,            // Cost Basis
    margin,          // Gross Margin $
    marginPct + '%', // Margin %
    orderId,         // Order/Transaction ID
  ]);
}

// ── DAILY AUDIT: RECONCILE CATALOG VS WOOCOMMERCE ─────────────────

function dailyStatusAudit() {
  const cfg = getConfig_();
  const sheet = SpreadsheetApp.openById(cfg.MASTER_CATALOG_ID).getSheetByName(CATALOG_TAB);
  const data = sheet.getDataRange().getValues();

  let outOfSync = 0;

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const wcId = row[COL.WC_ID];
    const catalogStatus = row[COL.STATUS_SITE];

    if (!wcId || catalogStatus === 'SOLD') continue;

    try {
      const wcProduct = wcApiRequest('GET', `/wp-json/wc/v3/products/${wcId}`);

      // If WC says out of stock but catalog says active - flag it
      if (wcProduct.stock_status === 'outofstock' && catalogStatus === 'Active') {
        sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Status mismatch');
        outOfSync++;
      }
    } catch (e) {
      // Product may have been deleted in WC
      if (e.message.includes('404')) {
        sheet.getRange(i + 1, COL.WC_ID + 1).setValue('');
        sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Pending');
      }
    }

    Utilities.sleep(200);
  }

  Logger.log(`Daily audit complete. Out-of-sync items flagged: ${outOfSync}`);
}

// ── WEEKLY REPORT ──────────────────────────────────────────────────

function weeklyReport() {
  const cfg = getConfig_();
  const ss = SpreadsheetApp.openById(cfg.SALES_TRACKER_ID);
  const sheet = ss.getSheetByName(SALES_TAB) || ss.getSheets()[0];
  const data = sheet.getDataRange().getValues();

  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

  let totalRevenue = 0, totalMargin = 0, units = 0;
  const byPlatform = {};

  for (let i = 1; i < data.length; i++) {
    const saleDate = new Date(data[i][0]);
    if (saleDate < oneWeekAgo) continue;

    const platform = data[i][6];
    const revenue = parseFloat(data[i][7]) || 0;
    const margin = parseFloat(data[i][9]) || 0;

    totalRevenue += revenue;
    totalMargin += margin;
    units++;

    byPlatform[platform] = byPlatform[platform] || { revenue: 0, units: 0 };
    byPlatform[platform].revenue += revenue;
    byPlatform[platform].units++;
  }

  let report = `HEAT4YAFEAT Weekly Report - ${new Date().toDateString()}\n`;
  report += `${'-'.repeat(40)}\n`;
  report += `Units Sold: ${units}\n`;
  report += `Total Revenue: $${totalRevenue.toFixed(2)}\n`;
  report += `Total Gross Margin: $${totalMargin.toFixed(2)}\n`;
  report += `Average Margin: ${units > 0 ? ((totalMargin / totalRevenue) * 100).toFixed(1) : 0}%\n\n`;
  report += `By Platform:\n`;
  Object.entries(byPlatform).forEach(([p, d]) => {
    report += `  ${p}: ${d.units} units | $${d.revenue.toFixed(2)}\n`;
  });

  Logger.log(report);
  // Optionally email: MailApp.sendEmail('owner@example.com', 'H4YF Weekly Report', report);
}

// ── HELPER: BUILD WOOCOMMERCE PRODUCT PAYLOAD ─────────────────────

function buildWcProductPayload(row) {
  const brand = row[COL.BRAND];
  const model = row[COL.MODEL];
  const colorway = row[COL.COLORWAY];
  const size = row[COL.SIZE];
  const condition = row[COL.CONDITION];
  const price = row[COL.PRICE];
  const description = row[COL.DESCRIPTION];
  const sku = row[COL.SKU];
  const imageUrl = row[COL.IMAGE_URL];
  const gtin = row[COL.GTIN];
  const categoryName = row[COL.CATEGORY];
  const tags = row[COL.TAGS] ? row[COL.TAGS].split(',').map((t) => ({ name: t.trim() })) : [];

  const name = `${brand} ${model} ${colorway} Size ${size}`;

  const payload = {
    name: name,
    sku: sku,
    status: 'publish',
    catalog_visibility: 'visible',
    type: 'simple',
    regular_price: String(price),
    description: description || buildDefaultDescription(brand, model, colorway, size, condition),
    short_description: `${brand} ${model} | ${colorway} | Size ${size} | ${condition} | HEAT4YAFEAT Authenticated`,
    stock_status: 'instock',
    manage_stock: false,
    tags: tags,
    attributes: [
      { name: 'Brand', options: [brand], visible: true },
      { name: 'Model', options: [model], visible: true },
      { name: 'Colorway', options: [colorway], visible: true },
      { name: 'Size', options: [String(size)], visible: true },
      { name: 'Condition', options: [condition], visible: true },
    ],
    meta_data: [
      { key: '_authentication_status', value: 'HEAT4YAFEAT Certified' },
    ],
  };

  if (gtin) {
    payload.global_unique_id = String(gtin);
  }
  if (imageUrl) {
    payload.images = [{ src: imageUrl, alt: name }];
  }

  const catId = getCategoryId(categoryName);
  if (catId) {
    payload.categories = [{ id: catId }];
  }

  return payload;
}

function buildDefaultDescription(brand, model, colorway, size, condition) {
  return `
<p>This ${brand} ${model} in the ${colorway} colorway has been through HEAT4YAFEAT's
rigorous authentication process. Every pair we sell is verified authentic - no exceptions.</p>

<p><strong>Details:</strong></p>
<ul>
<li>Brand: ${brand}</li>
<li>Model: ${model}</li>
<li>Colorway: ${colorway}</li>
<li>Size: US Men's ${size}</li>
<li>Condition: ${condition}</li>
<li>Authentication: HEAT4YAFEAT Certified</li>
</ul>

<p><strong>Why buy from HEAT4YAFEAT?</strong><br>
267 authenticated sales. 100% positive feedback. Indianapolis's trusted sneaker curator since 2016.
We authenticate every pair before it reaches you - no fakes, no shortcuts, no exceptions.</p>

<p>Questions? Message us before or after purchase. We stand behind every pair.</p>
<p><em>Split into 4 interest-free payments with Klarna or Afterpay at checkout.</em></p>
`;
}

// WC Category ID map (from getCategoryIds() run — populate after real IDs are confirmed)
function getCategoryId(categoryName) {
  const catMap = {
    'Air Jordan': 16, 'AJ1': 24, 'AJ2': 25, 'AJ3': 26, 'AJ4': 27,
    'AJ5': 28, 'AJ6': 29, 'AJ7': 30, 'AJ8': 31, 'AJ9': 32,
    'AJ10': 33, 'AJ11': 34, 'AJ12': 35, 'AJ13': 36, 'AJ14': 37,
    'AJ15': 38, 'AJ16+': 39, 'Kobe 4 Protro': 40, 'Kobe 5': 41,
    'Kobe 6': 42, 'Kobe 8': 43, 'Kobe 9': 44, 'Mambacurial': 45,
    'Phantom': 46, 'Nike Kobe': 17, 'Nike Kobe Other': 47,
    'LeBron Signature': 18, 'Nike Collab': 19, 'Nike SB': 20,
    'Reebok': 22, 'Vintage Streetwear': 21, 'Variety': 23,
    'Uncategorized': 15,
  };
  return catMap[categoryName] || 15;
}

// ── HELPER: WC API REQUEST ─────────────────────────────────────────

function wcApiRequest(method, endpoint, payload) {
  const cfg = getConfig_();
  const url = cfg.WC_BASE_URL + endpoint;
  const auth = Utilities.base64Encode(cfg.WC_CONSUMER_KEY + ':' + cfg.WC_CONSUMER_SECRET);

  const options = {
    method: method.toLowerCase(),
    headers: {
      Authorization: 'Basic ' + auth,
      'Content-Type': 'application/json',
    },
    muteHttpExceptions: true,
  };

  if (payload && method !== 'GET') {
    options.payload = JSON.stringify(payload);
  }

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  const body = JSON.parse(response.getContentText());

  if (code < 200 || code >= 300) {
    throw new Error(`WC API ${method} ${endpoint} returned ${code}: ${body.message || JSON.stringify(body)}`);
  }

  return body;
}

// WordPress REST API (for pages, posts, menus)
function wpApiRequest(method, endpoint, payload) {
  const cfg = getConfig_();
  const url = cfg.WC_BASE_URL + endpoint;
  const auth = Utilities.base64Encode(cfg.WP_ADMIN_USER + ':' + cfg.WP_APP_PASSWORD);

  const options = {
    method: method.toLowerCase(),
    headers: {
      Authorization: 'Basic ' + auth,
      'Content-Type': 'application/json',
    },
    muteHttpExceptions: true,
  };

  if (payload && method !== 'GET') {
    options.payload = JSON.stringify(payload);
  }

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  const body = JSON.parse(response.getContentText());

  if (code < 200 || code >= 300) {
    throw new Error(`WP API ${method} ${endpoint} returned ${code}: ${JSON.stringify(body)}`);
  }

  return body;
}

// ── UTILITY: FLAG ALL ACTIVE ITEMS AS PENDING (force full re-sync) ─

function flagAllAsPending() {
  const cfg = getConfig_();
  const sheet = SpreadsheetApp.openById(cfg.MASTER_CATALOG_ID).getSheetByName(CATALOG_TAB);
  const data = sheet.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    if (data[i][COL.STATUS_SITE] !== 'SOLD') {
      sheet.getRange(i + 1, COL.SYNC_STATUS + 1).setValue('Pending');
    }
  }
  Logger.log('All active items flagged as Pending. Next sync will push all to WooCommerce.');
}
