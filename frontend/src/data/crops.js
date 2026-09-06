/**
 * Crop Master Data — 89 India-relevant crop types.
 * Source: crop_types_india_90.csv
 *
 * Categories: Cereal, Pulse, Oilseed, Cash Crop, Fiber Crop,
 *             Plantation, Spice, Vegetable, Tuber, Fruit
 *
 * Each crop carries:
 *   name  — English (also what is stored in the backend)
 *   te    — Telugu name (వరి, శనగలు …)
 *   hi    — Hindi name (धान, चना …)
 *   emoji — a simple picture farmers recognise (🌾 వరి, 🥔 బంగాళాదుంప …)
 *
 * Use localizeCrop(cropName, lang) to render the name in the farmer's
 * language (falls back to English for unknown crops) and cropEmoji(name)
 * for the picture.
 */

export const CROP_CATEGORIES = [
  'Cereal', 'Pulse', 'Oilseed', 'Cash Crop', 'Fiber Crop',
  'Plantation', 'Spice', 'Vegetable', 'Tuber', 'Fruit',
];

export const CROPS = [
  // Cereals (15)
  { name: 'Paddy', te: 'వరి', hi: 'धान', emoji: '🌾', category: 'Cereal' },
  { name: 'Wheat', te: 'గోధుమ', hi: 'गेहूँ', emoji: '🌾', category: 'Cereal' },
  { name: 'Maize', te: 'మొక్కజొన్న', hi: 'मक्का', emoji: '🌽', category: 'Cereal' },
  { name: 'Barley', te: 'బార్లీ', hi: 'जौ', emoji: '🌾', category: 'Cereal' },
  { name: 'Sorghum (Jowar)', te: 'జొన్న', hi: 'ज्वार', emoji: '🌾', category: 'Cereal' },
  { name: 'Pearl Millet (Bajra)', te: 'సజ్జలు', hi: 'बाजरा', emoji: '🌾', category: 'Cereal' },
  { name: 'Finger Millet (Ragi)', te: 'రాగులు', hi: 'रागी', emoji: '🌾', category: 'Cereal' },
  { name: 'Foxtail Millet', te: 'కొర్రలు', hi: 'कंगनी', emoji: '🌾', category: 'Cereal' },
  { name: 'Little Millet', te: 'సామలు', hi: 'कुटकी', emoji: '🌾', category: 'Cereal' },
  { name: 'Kodo Millet', te: 'అరికెలు', hi: 'कोदो', emoji: '🌾', category: 'Cereal' },
  { name: 'Barnyard Millet', te: 'ఉద్దలు', hi: 'सामा', emoji: '🌾', category: 'Cereal' },
  { name: 'Proso Millet', te: 'వరిగెలు', hi: 'चीना', emoji: '🌾', category: 'Cereal' },
  { name: 'Browntop Millet', te: 'అండ్రు', hi: 'ब्राउनटॉप मिलेट', emoji: '🌾', category: 'Cereal' },
  { name: 'Oat', te: 'ఓట్స్', hi: 'जई', emoji: '🌾', category: 'Cereal' },
  { name: 'Buckwheat', te: 'కుట్టు', hi: 'कुट्टू', emoji: '🌾', category: 'Cereal' },
  // Pulses (9)
  { name: 'Red Gram (Tur/Arhar)', te: 'కందులు', hi: 'अरहर (तूर)', emoji: '🫘', category: 'Pulse' },
  { name: 'Black Gram (Urad)', te: 'మినుములు', hi: 'उड़द', emoji: '🫘', category: 'Pulse' },
  { name: 'Green Gram (Moong)', te: 'పెసర్లు', hi: 'मूंग', emoji: '🫘', category: 'Pulse' },
  { name: 'Bengal Gram (Chickpea/Chana)', te: 'శనగలు', hi: 'चना', emoji: '🫘', category: 'Pulse' },
  { name: 'Lentil (Masoor)', te: 'మసూర్ పప్పు', hi: 'मसूर', emoji: '🫘', category: 'Pulse' },
  { name: 'Field Pea', te: 'బఠానీ', hi: 'मटर', emoji: '🫛', category: 'Pulse' },
  { name: 'Cowpea (Lobia)', te: 'అలసందలు', hi: 'लोबिया', emoji: '🫘', category: 'Pulse' },
  { name: 'Horse Gram', te: 'ఉలవలు', hi: 'कुल्थी', emoji: '🫘', category: 'Pulse' },
  { name: 'Moth Bean', te: 'మోత్ బీన్', hi: 'मोठ', emoji: '🫘', category: 'Pulse' },
  // Oilseeds (9)
  { name: 'Soybean', te: 'సోయాబీన్', hi: 'सोयाबीन', emoji: '🫘', category: 'Oilseed' },
  { name: 'Groundnut', te: 'వేరుశనగ', hi: 'मूंगफली', emoji: '🥜', category: 'Oilseed' },
  { name: 'Sunflower', te: 'పొద్దుతిరుగుడు', hi: 'सूरजमुखी', emoji: '🌻', category: 'Oilseed' },
  { name: 'Sesame', te: 'నువ్వులు', hi: 'तिल', emoji: '🌱', category: 'Oilseed' },
  { name: 'Mustard', te: 'ఆవాలు', hi: 'सरसों', emoji: '🌼', category: 'Oilseed' },
  { name: 'Safflower', te: 'కుసుమ', hi: 'कुसुम', emoji: '🌸', category: 'Oilseed' },
  { name: 'Castor', te: 'ఆముదం', hi: 'अरंडी', emoji: '🌿', category: 'Oilseed' },
  { name: 'Linseed', te: 'అవిసెలు', hi: 'अलसी', emoji: '🌿', category: 'Oilseed' },
  { name: 'Niger Seed', te: 'నూక నువ్వులు', hi: 'रामतिल', emoji: '🌱', category: 'Oilseed' },
  // Cash Crops (3)
  { name: 'Cotton', te: 'పత్తి', hi: 'कपास', emoji: '☁️', category: 'Cash Crop' },
  { name: 'Sugarcane', te: 'చెరకు', hi: 'गन्ना', emoji: '🎋', category: 'Cash Crop' },
  { name: 'Tobacco', te: 'పొగాకు', hi: 'तम्बाकू', emoji: '🌿', category: 'Cash Crop' },
  // Fiber Crops (2)
  { name: 'Jute', te: 'జనుము', hi: 'जूट', emoji: '🌿', category: 'Fiber Crop' },
  { name: 'Mesta', te: 'మెస్టా', hi: 'मेस्टा', emoji: '🌿', category: 'Fiber Crop' },
  // Plantation (5)
  { name: 'Tea', te: 'తేయాకు', hi: 'चाय', emoji: '🍵', category: 'Plantation' },
  { name: 'Coffee', te: 'కాఫీ', hi: 'कॉफ़ी', emoji: '☕', category: 'Plantation' },
  { name: 'Coconut', te: 'కొబ్బరి', hi: 'नारियल', emoji: '🥥', category: 'Plantation' },
  { name: 'Arecanut', te: 'వక్క', hi: 'सुपारी', emoji: '🌰', category: 'Plantation' },
  { name: 'Rubber', te: 'రబ్బర్', hi: 'रबड़', emoji: '🌳', category: 'Plantation' },
  // Spices (11)
  { name: 'Pepper', te: 'మిరియాలు', hi: 'काली मिर्च', emoji: '⚫', category: 'Spice' },
  { name: 'Cardamom', te: 'యాలకులు', hi: 'इलायची', emoji: '🟢', category: 'Spice' },
  { name: 'Turmeric', te: 'పసుపు', hi: 'हल्दी', emoji: '🟡', category: 'Spice' },
  { name: 'Cumin', te: 'జీలకర్ర', hi: 'जीरा', emoji: '🟤', category: 'Spice' },
  { name: 'Coriander', te: 'ధనియాలు', hi: 'धनिया', emoji: '🌿', category: 'Spice' },
  { name: 'Chilli', te: 'మిరపకాయలు', hi: 'मिर्च', emoji: '🌶️', category: 'Spice' },
  { name: 'Fenugreek', te: 'మెంతులు', hi: 'मेथी', emoji: '🌿', category: 'Spice' },
  { name: 'Ginger', te: 'అల్లం', hi: 'अदरक', emoji: '🫚', category: 'Spice' },
  { name: 'Garlic', te: 'వెల్లుల్లి', hi: 'लहसुन', emoji: '🧄', category: 'Spice' },
  { name: 'Tamarind', te: 'చింతపండు', hi: 'इमली', emoji: '🟤', category: 'Spice' },
  // Vegetables (18)
  { name: 'Potato', te: 'బంగాళాదుంప', hi: 'आलू', emoji: '🥔', category: 'Vegetable' },
  { name: 'Tomato', te: 'టమాటా', hi: 'टमाटर', emoji: '🍅', category: 'Vegetable' },
  { name: 'Onion', te: 'ఉల్లిపాయ', hi: 'प्याज़', emoji: '🧅', category: 'Vegetable' },
  { name: 'Brinjal (Eggplant)', te: 'వంకాయ', hi: 'बैंगन', emoji: '🍆', category: 'Vegetable' },
  { name: "Okra (Lady's Finger)", te: 'బెండకాయ', hi: 'भिंडी', emoji: '🫑', category: 'Vegetable' },
  { name: 'Cabbage', te: 'క్యాబేజీ', hi: 'पत्ता गोभी', emoji: '🥬', category: 'Vegetable' },
  { name: 'Cauliflower', te: 'కాలీఫ్లవర్', hi: 'फूल गोभी', emoji: '🥦', category: 'Vegetable' },
  { name: 'Carrot', te: 'క్యారెట్', hi: 'गाजर', emoji: '🥕', category: 'Vegetable' },
  { name: 'Radish', te: 'ముల్లంగి', hi: 'मूली', emoji: '🫜', category: 'Vegetable' },
  { name: 'Beetroot', te: 'బీట్రూట్', hi: 'चुकंदर', emoji: '🫜', category: 'Vegetable' },
  { name: 'Bottle Gourd', te: 'సొరకాయ', hi: 'लौकी', emoji: '🥒', category: 'Vegetable' },
  { name: 'Bitter Gourd', te: 'కాకరకాయ', hi: 'करेला', emoji: '🥒', category: 'Vegetable' },
  { name: 'Ridge Gourd', te: 'బీరకాయ', hi: 'तोरई', emoji: '🥒', category: 'Vegetable' },
  { name: 'Pumpkin', te: 'గుమ్మడికాయ', hi: 'कद्दू', emoji: '🎃', category: 'Vegetable' },
  { name: 'Cucumber', te: 'దోసకాయ', hi: 'खीरा', emoji: '🥒', category: 'Vegetable' },
  { name: 'Green Peas', te: 'బఠానీలు', hi: 'हरी मटर', emoji: '🫛', category: 'Vegetable' },
  { name: 'French Bean', te: 'ఫ్రెంచ్ బీన్స్', hi: 'फ्रेंच बीन', emoji: '🫛', category: 'Vegetable' },
  { name: 'Drumstick', te: 'మునగకాయ', hi: 'सहजन', emoji: '🫛', category: 'Vegetable' },
  { name: 'Sweet Potato', te: 'చిలగడదుంప', hi: 'शकरकंद', emoji: '🍠', category: 'Vegetable' },
  // Tubers (1)
  { name: 'Tapioca (Cassava)', te: 'కర్రపెండలం', hi: 'कसावा', emoji: '🫜', category: 'Tuber' },
  // Fruits (15)
  { name: 'Banana', te: 'అరటిపండు', hi: 'केला', emoji: '🍌', category: 'Fruit' },
  { name: 'Mango', te: 'మామిడిపండు', hi: 'आम', emoji: '🥭', category: 'Fruit' },
  { name: 'Guava', te: 'జామపండు', hi: 'अमरूद', emoji: '🍐', category: 'Fruit' },
  { name: 'Papaya', te: 'బొప్పాయి', hi: 'पपीता', emoji: '🍈', category: 'Fruit' },
  { name: 'Pomegranate', te: 'దానిమ్మ', hi: 'अनार', emoji: '🍎', category: 'Fruit' },
  { name: 'Grapes', te: 'ద్రాక్ష', hi: 'अंगूर', emoji: '🍇', category: 'Fruit' },
  { name: 'Orange', te: 'నారింజ', hi: 'संतरा', emoji: '🍊', category: 'Fruit' },
  { name: 'Sweet Lime (Mosambi)', te: 'బత్తాయి', hi: 'मौसंबी', emoji: '🍋🟩', category: 'Fruit' },
  { name: 'Lemon', te: 'నిమ్మకాయ', hi: 'नींबू', emoji: '🍋', category: 'Fruit' },
  { name: 'Watermelon', te: 'పుచ్చకాయ', hi: 'तरबूज़', emoji: '🍉', category: 'Fruit' },
  { name: 'Muskmelon', te: 'ఖర్బూజా', hi: 'खरबूजा', emoji: '🍈', category: 'Fruit' },
  { name: 'Pineapple', te: 'అనాస', hi: 'अनानास', emoji: '🍍', category: 'Fruit' },
  { name: 'Apple', te: 'యాపిల్', hi: 'सेब', emoji: '🍏', category: 'Fruit' },
  { name: 'Sapota (Chikoo)', te: 'సపోటా', hi: 'चीकू', emoji: '🟤', category: 'Fruit' },
  { name: 'Jackfruit', te: 'పనస', hi: 'कटहल', emoji: '🟡', category: 'Fruit' },
  { name: 'Custard Apple', te: 'సీతాఫలం', hi: 'शरीफा', emoji: '🥝', category: 'Fruit' },
];

/* Localized category names (Telugu / Hindi) — used by the crop picker. */
const CATEGORY_NAMES = {
  en: {
    Cereal: 'Cereal', Pulse: 'Pulse', Oilseed: 'Oilseed', 'Cash Crop': 'Cash Crop',
    'Fiber Crop': 'Fiber Crop', Plantation: 'Plantation', Spice: 'Spice',
    Vegetable: 'Vegetable', Tuber: 'Tuber', Fruit: 'Fruit', Other: 'Other',
  },
  te: {
    Cereal: 'ధాన్యాలు', Pulse: 'పప్పులు', Oilseed: 'నూనె గింజలు', 'Cash Crop': 'నగదు పంట',
    'Fiber Crop': 'నార పంట', Plantation: 'తోట పంట', Spice: 'సుగంధ ద్రవ్యాలు',
    Vegetable: 'కూరగాయలు', Tuber: 'దుంప పంట', Fruit: 'పండ్లు', Other: 'ఇతర',
  },
  hi: {
    Cereal: 'अनाज', Pulse: 'दालें', Oilseed: 'तिलहन', 'Cash Crop': 'नकदी फसल',
    'Fiber Crop': 'रेशे की फसल', Plantation: 'बागान', Spice: 'मसाले',
    Vegetable: 'सब्ज़ियाँ', Tuber: 'कंद', Fruit: 'फल', Other: 'अन्य',
  },
};

/** Display a crop category in the farmer's language. */
export function localizeCategory(category, lang) {
  const table = CATEGORY_NAMES[lang] || CATEGORY_NAMES.en;
  return table[category] || category;
}

/** Quick lookup: crop name → category. Returns 'Other' for unknown crops. */
export function getCropCategory(cropName) {
  const found = CROPS.find((c) => c.name === cropName);
  return found ? found.category : 'Other';
}

/**
 * Display a crop name in the farmer's language.
 * @param {string} cropName English name (as stored in the backend)
 * @param {string} lang     'en' | 'te' | 'hi'
 * @returns {string} Localized name; English fallback for unknown crops.
 */
export function localizeCrop(cropName, lang) {
  if (!cropName) return cropName;
  if (lang !== 'te' && lang !== 'hi') return cropName;

  const key = String(cropName).trim().toLowerCase();
  let found = CROPS.find((c) => c.name.toLowerCase() === key);
  // Fallback: match without the parenthetical alias, e.g. "Sorghum" vs "Sorghum (Jowar)"
  if (!found && key.includes(' (')) {
    const base = key.split(' (')[0];
    found = CROPS.find((c) => c.name.toLowerCase().split(' (')[0] === base);
  }
  return (found && found[lang]) || cropName;
}

/** Emoji picture for a crop (English name lookup). Returns 🌾 for unknown. */
export function cropEmoji(cropName) {
  if (!cropName) return '🌾';
  const key = String(cropName).trim().toLowerCase();
  let found = CROPS.find((c) => c.name.toLowerCase() === key);
  if (!found && key.includes(' (')) {
    const base = key.split(' (')[0];
    found = CROPS.find((c) => c.name.toLowerCase().split(' (')[0] === base);
  }
  return (found && found.emoji) || '🌾';
}

/**
 * Does a crop (by English name) match a search query in the current language?
 * Matches English, Telugu and Hindi names so voice/typed search works in
 * the farmer's own language.
 */
export function cropMatchesQuery(cropName, query, lang = 'en') {
  const q = String(query || '').toLowerCase().trim();
  if (!q) return true;
  const names = [cropName, localizeCrop(cropName, 'te'), localizeCrop(cropName, 'hi')];
  return names.some((n) => n && n.toLowerCase().includes(q));
}

/** Does a category match a query (in any language)? */
export function categoryMatchesQuery(category, query, lang = 'en') {
  const q = String(query || '').toLowerCase().trim();
  if (!q) return true;
  const names = [category, localizeCategory(category, 'te'), localizeCategory(category, 'hi')];
  return names.some((n) => n && n.toLowerCase().includes(q));
}

/** Category display — text only (no emoji). */
export const CATEGORY_EMOJI = {
  Cereal: 'Cereal', Pulse: 'Pulse', Oilseed: 'Oilseed', 'Cash Crop': 'Cash Crop',
  'Fiber Crop': 'Fiber Crop', Plantation: 'Plantation', Spice: 'Spice', Vegetable: 'Vegetable',
  Tuber: 'Tuber', Fruit: 'Fruit', Other: 'Other',
};

/** Filter crops by search term (case-insensitive, matches local names too). */
export function searchCrops(query, category, lang = 'en') {
  const q = (query || '').toLowerCase().trim();
  return CROPS.filter((c) => {
    if (category && c.category !== category) return false;
    if (!q) return true;
    return cropMatchesQuery(c.name, q, lang);
  });
}