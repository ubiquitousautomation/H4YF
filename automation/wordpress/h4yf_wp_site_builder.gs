/**
 * H4YF — WordPress Site Builder & Page Content Engine
 * h4yf_wp_site_builder.gs
 *
 * PURPOSE: Pushes page content and navigation menu structure to the live
 * WordPress site via REST API. Run updateAllPages() after content changes
 * in the site content source doc; run createNavigationMenus() once.
 *
 * SECURITY — READ BEFORE RUNNING:
 * This script reads credentials from Apps Script's PropertiesService
 * instead of hardcoding them, so nothing sensitive is ever committed.
 * Set these once per Apps Script project:
 *
 *   Extensions -> Apps Script -> Project Settings -> Script Properties
 *     H4YF_WP_BASE_URL      = https://your-site.example.com
 *     H4YF_WP_ADMIN_USER    = your-wp-username
 *     H4YF_WP_APP_PASSWORD  = xxxx xxxx xxxx xxxx xxxx xxxx
 *
 * HOW TO GET A WP APP PASSWORD:
 *   WP Admin -> Users -> Your Profile -> scroll to "Application Passwords"
 *   Name: "H4YF Apps Script" -> Add New Application Password -> copy the key
 *
 * PAGE CONTENT: This script pushes page HTML by ID (see PAGE_IDS below).
 * The actual HTML bodies for each page are long-form generated content
 * (About, FAQ, Authentication, Shipping, Trusted Partners, Contact) —
 * source them from the WordPress site content doc in Drive
 * (06 — AUTOMATION SCRIPTS & TOOLS) and paste into getPageContent() below,
 * or point this at a Drive doc/sheet as the content source instead of
 * inlining HTML in the script (recommended — keeps content edits out of
 * code review).
 *
 * Ubiquitous Solutions | HEAT4YAFEAT | 2026
 */

function getConfig_() {
  const props = PropertiesService.getScriptProperties();
  const cfg = {
    BASE_URL: props.getProperty('H4YF_WP_BASE_URL'),
    ADMIN_USER: props.getProperty('H4YF_WP_ADMIN_USER'),
    APP_PASSWORD: props.getProperty('H4YF_WP_APP_PASSWORD'),
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

// WordPress Page IDs (from the June 2026 site build)
const PAGE_IDS = {
  about: 812,
  faq: 813,
  authentication: 814,
  shipping: 815,
  trusted_partners: 816,
  mystery_sneaker: 817,
  contact: 818,
  members: 819,
};

/**
 * Page content source. Returns { [key]: { title, content } } keyed to
 * PAGE_IDS above. Left as a stub — see the header comment for how to
 * source the real HTML (either paste it here per page, or swap this
 * function to pull from a Drive doc/sheet at runtime).
 */
function getPageContent() {
  return {
    // about: { title: 'About HEAT4YAFEAT', content: '<!-- wp:group -->...' },
    // faq: { title: 'Frequently Asked Questions', content: '...' },
    // authentication: { title: 'Authentication Process', content: '...' },
    // shipping: { title: 'Shipping & Returns', content: '...' },
    // trusted_partners: { title: 'Trusted Partners', content: '...' },
    // contact: { title: 'Contact', content: '...' },
  };
}

/**
 * MASTER RUNNER — pushes every page defined in getPageContent().
 */
function updateAllPages() {
  const pages = getPageContent();
  const keys = Object.keys(pages);
  if (!keys.length) {
    Logger.log('getPageContent() returned no pages — populate it first (see header comment).');
    return;
  }
  keys.forEach((key) => {
    const id = PAGE_IDS[key];
    const page = pages[key];
    if (!id || !page) return;
    try {
      wpRequest('POST', `/wp-json/wp/v2/pages/${id}`, {
        title: page.title,
        content: page.content,
        status: 'publish',
      });
      Logger.log(`Updated page: ${page.title} (ID: ${id})`);
      Utilities.sleep(500);
    } catch (e) {
      Logger.log(`Failed to update ${page.title}: ${e.message}`);
    }
  });
}

/**
 * Prints the intended navigation structure. WP core REST API does not
 * expose menu creation — either install a REST API Menus plugin, or
 * create these manually: Appearance -> Menus.
 */
function createNavigationMenus() {
  const primaryItems = [
    { title: 'Shop', url: '/shop', order: 1 },
    { title: 'Authentication', url: '/authentication', order: 2 },
    { title: 'About', url: '/about', order: 3 },
    { title: 'Whatnot Shows', url: 'https://whatnot.com/user/heat4yafeat', order: 4 },
    { title: 'FAQ', url: '/faq', order: 5 },
    { title: 'Contact', url: '/contact', order: 6 },
  ];

  const footerItems = [
    { title: 'Returns & Shipping', url: '/shipping-returns', order: 1 },
    { title: 'Authentication', url: '/authentication', order: 2 },
    { title: 'Privacy Policy', url: '/privacy-policy', order: 3 },
    { title: 'Contact', url: '/contact', order: 4 },
  ];

  Logger.log('Menu creation via REST API requires a REST API Menus plugin.');
  Logger.log('Primary nav items: ' + JSON.stringify(primaryItems));
  Logger.log('Footer nav items: ' + JSON.stringify(footerItems));
  Logger.log('Create these manually under Appearance -> Menus if the plugin is not installed.');
}

/**
 * WP REST API request helper. Credentials come from getConfig_(),
 * never hardcoded.
 */
function wpRequest(method, endpoint, payload) {
  const cfg = getConfig_();
  const url = cfg.BASE_URL + endpoint;
  const auth = Utilities.base64Encode(cfg.ADMIN_USER + ':' + cfg.APP_PASSWORD);

  const options = {
    method: method.toLowerCase(),
    headers: {
      Authorization: 'Basic ' + auth,
      'Content-Type': 'application/json',
    },
    payload: payload ? JSON.stringify(payload) : undefined,
    muteHttpExceptions: true,
  };

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  const body = JSON.parse(response.getContentText());

  if (code < 200 || code >= 300) {
    throw new Error(`${code}: ${JSON.stringify(body)}`);
  }
  return body;
}
