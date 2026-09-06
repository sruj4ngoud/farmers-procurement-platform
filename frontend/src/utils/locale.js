/**
 * Localizing text that originates from the backend (data, not UI keys).
 * The database stores English strings; these helpers translate the known
 * patterns at render time so the farmer always sees their language.
 */

const CENTRE_SUFFIX = {
  en: { 'procurement centre': 'Procurement Centre', 'procurement center': 'Procurement Centre', centre: 'Centre', center: 'Centre' },
  te: { 'procurement centre': 'కొనుగోలు కేంద్రం', 'procurement center': 'కొనుగోలు కేంద్రం', centre: 'కేంద్రం', center: 'కేంద్రం' },
  hi: { 'procurement centre': 'खरीद केंद्र', 'procurement center': 'खरीद केंद्र', centre: 'केंद्र', center: 'केंद्र' },
};

/**
 * Translate a centre name such as "Sangareddy Procurement Centre".
 * Place names stay the same; only the descriptive suffix is translated.
 */
export function localizeCentre(centreName, lang) {
  if (!centreName) return centreName;
  if (lang !== 'te' && lang !== 'hi') return centreName;

  const suffixes = CENTRE_SUFFIX[lang];
  let out = String(centreName);
  // Longest first so "Procurement Centre" wins over "Centre".
  const patterns = [
    ['procurement centre', 'procurement center'],
    ['centre', 'center'],
  ];
  for (const group of patterns) {
    const match = group.find((p) => out.toLowerCase().includes(p));
    if (match) {
      out = out.replace(new RegExp(match, 'i'), suffixes[match]);
      break;
    }
  }
  return out;
}

/* Notification title translations, keyed by the exact English title. */
const NOTIF_TITLES = {
  'Booking confirmed': { te: 'బుకింగ్ నిర్ధారించబడింది', hi: 'बुकिंग पक्की हो गई' },
  'Queue token generated': { te: 'క్యూ టోకెన్ జనరేట్ అయింది', hi: 'क्यू टोकन बन गया' },
  'Procurement completed': { te: 'కొనుగోలు పూర్తయింది', hi: 'खरीद पूरी हो गई' },
  'Payment processed': { te: 'చెల్లింపు ప్రాసెస్ అయింది', hi: 'भुगतान हो गया' },
  'Booking Review Update': { te: 'బుకింగ్ సమీక్ష నవీకరణ', hi: 'बुकिंग समीक्षा अपडेट' },
  'Booking Created': { te: 'బుకింగ్ సృష్టించబడింది', hi: 'बुकिंग बनाई गई' },
  'Booking Rejected': { te: 'బుకింగ్ తిరస్కరించబడింది', hi: 'बुकिंग अस्वीकृत' },
  'Booking Accepted': { te: 'బుకింగ్ ఆమోదించబడింది', hi: 'बुकिंग स्वीकृत' },
};

const sub = (template, vars) =>
  Object.entries(vars).reduce(
    (s, [k, v]) => s.split(`{${k}}`).join(v != null ? String(v) : ''),
    template
  );

/* Message translation rules: [regex, template(te), template(hi)]. */
const NOTIF_MESSAGES = [
  [
    /^Booking (\S+) for ([\d.]+) quintals has been confirmed\.?$/,
    '{b} కోసం {q} క్వింటాళ్లు నిర్ధారించబడ్డాయి.',
    '{b} के लिए {q} क्विंटल पक्की हुई।',
    (m) => ({ b: m[1], q: m[2] }),
  ],
  [
    /^Your queue token (\d+) has been generated\. Keep this booking number handy: ([A-Z]{2}[A-Z0-9-]*)\.?$/,
    'మీ క్యూ టోకెన్ {t} జనరేట్ అయింది. ఈ బుకింగ్ నంబర్ దగ్గర ఉంచుకోండి: {b}.',
    'आपका क्यू टोकन {t} बन गया है। यह बुकिंग नंबर संभाल कर रखें: {b}।',
    (m) => ({ t: m[1], b: m[2] }),
  ],
  [
    /^Your produce was procured successfully: ([\d.]+) quintals accepted at ([\d.]+) per quintal\.?$/,
    'మీ పంట విజయవంతంగా కొనుగోలు చేయబడింది: {q} క్వింటాళ్లు ఆమోదించబడ్డాయి, క్వింటాలుకు ₹{p}.',
    'आपकी उपज सफलतापूर्वक खरीदी गई: {q} क्विंटल स्वीकृत, ₹{p} प्रति क्विंटल।',
    (m) => ({ q: m[1], p: m[2] }),
  ],
  [
    /^A government payment of ([\d.,]+) has been credited to your account(?: \(Ref: (\S+)\))?\.?$/,
    'మీ ఖాతాకు ₹{a} ప్రభుత్వ చెల్లింపు జమ అయింది{ref}.',
    'आपके खाते में ₹{a} सरकारी भुगतान जमा हुआ{ref}।',
    (m) => ({ a: m[1], ref: m[2] ? ` (Ref: ${m[2]})` : '' }),
  ],
  [
    /^Your booking (\S+) has been rejected\. Reason: (.+)$/,
    'మీ బుకింగ్ {b} తిరస్కరించబడింది. కారణం: {r}',
    'आपकी बुकिंग {b} अस्वीकृत हुई। कारण: {r}',
    (m) => ({ b: m[1], r: m[2] }),
  ],
  [
    /^Your booking (\S+) has been accepted\.?$/,
    'మీ బుకింగ్ {b} ఆమోదించబడింది.',
    'आपकी बुकिंग {b} स्वीकृत हो गई।',
    (m) => ({ b: m[1] }),
  ],
  [
    /^Your booking (\S+) was automatically accepted because it was not reviewed within 24 hours\.?$/,
    'మీ బుకింగ్ {b} 24 గంటల్లో సమీక్షించనందున స్వయంచాలకంగా ఆమోదించబడింది.',
    'आपकी बुकिंग {b} 24 घंटों में समीक्षा न होने पर स्वतः स्वीकृत हुई।',
    (m) => ({ b: m[1] }),
  ],
  [
    /^Your booking (\S+) has been created successfully\.?$/,
    'మీ బుకింగ్ {b} విజయవంతంగా సృష్టించబడింది.',
    'आपकी बुकिंग {b} सफलतापूर्वक बनाई गई।',
    (m) => ({ b: m[1] }),
  ],
];

/**
 * Localize a backend notification ({ title, message }) into the farmer's
 * language. Unknown titles/messages fall back to the original English text.
 */
export function localizeNotification(title, message, lang) {
  if (lang !== 'te' && lang !== 'hi') return { title, message };

  const tTitle = NOTIF_TITLES[title] ? NOTIF_TITLES[title][lang] : title;
  const msg = String(message || '').trim();
  let tMessage = message;

  for (const [re, teTpl, hiTpl, extract] of NOTIF_MESSAGES) {
    const m = msg.match(re);
    if (m) {
      const vars = extract(m);
      tMessage = sub(lang === 'te' ? teTpl : hiTpl, vars);
      break;
    }
  }
  return { title: tTitle, message: tMessage };
}