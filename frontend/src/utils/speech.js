/* ============================================================
   Speech helpers — Web Speech API (recognition + synthesis).
   All helpers degrade gracefully when the browser lacks support.
   ============================================================ */

export function isRecognitionSupported() {
  return typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function isSynthesisSupported() {
  return typeof window !== 'undefined' && !!window.speechSynthesis;
}

export function createRecognizer(langCode) {
  if (!isRecognitionSupported()) return null;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = langCode || 'en-IN';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.continuous = false;
  return rec;
}

/* ── Text-to-speech (with a tiny queue so reads don't cut each other) ── */

let speakQueue = [];
let currentlySpeaking = false;

function pickVoice(langCode) {
  if (!window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  const prefix = (langCode || 'en-IN').split('-')[0].toLowerCase();
  const match = voices.find((v) => v.lang.toLowerCase().startsWith(prefix) && v.localService);
  return match || voices.find((v) => v.lang.toLowerCase().startsWith(prefix)) || null;
}

function pump() {
  if (currentlySpeaking || speakQueue.length === 0) return;
  const job = speakQueue.shift();
  const utterance = new SpeechSynthesisUtterance(job.text);
  utterance.lang = job.lang;
  utterance.rate = 0.98;
  utterance.pitch = 1;
  const voice = pickVoice(job.lang);
  if (voice) utterance.voice = voice;
  utterance.onend = () => { currentlySpeaking = false; pump(); };
  utterance.onerror = () => { currentlySpeaking = false; pump(); };
  currentlySpeaking = true;
  window.speechSynthesis.speak(utterance);
}

/** Speak text aloud in the given BCP-47 language (default en-IN). */
export function speak(text, langCode = 'en-IN') {
  if (!text || !isSynthesisSupported()) return;
  speakQueue.push({ text, lang: langCode || 'en-IN' });
  pump();
}

export function stopSpeaking() {
  speakQueue = [];
  if (isSynthesisSupported()) window.speechSynthesis.cancel();
  currentlySpeaking = false;
}

/* ── Spoken numbers → digits (English / Telugu / Hindi) ── */

const EN_NUM = {
  zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7,
  eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13,
  fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18,
  nineteen: 19, twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60,
  seventy: 70, eighty: 80, ninety: 90, hundred: 100,
};

const TE_NUM = {
  సున్న: 0, ఒకటి: 1, రెండు: 2, మూడు: 3, నాలుగు: 4, ఐదు: 5, ఆరు: 6,
  ఏడు: 7, ఎనిమిది: 8, తొమ్మిది: 9, పది: 10, పదకొండు: 11, పన్నెండు: 12,
  పదమూడు: 13, పద్నాలుగు: 14, పదిహేను: 15, పదహారు: 16, పదిహేడు: 17,
  పద్దెనిమిది: 18, పంతొమ్మిది: 19, ఇరవై: 20, ముప్పై: 30, నలభై: 40,
  యాభై: 50, అరవై: 60, డెబ్బై: 70, ఎనభై: 80, తొంభై: 90, వంద: 100,
};

const HI_NUM = {
  शून्य: 0, एक: 1, दो: 2, तीन: 3, चार: 4, पाँच: 5, पांच: 5, छह: 6, छ: 6,
  सात: 7, आठ: 8, नौ: 9, दस: 10, ग्यारह: 11, बारह: 12, तेरह: 13,
  चौदह: 14, पंद्रह: 15, सोलह: 16, सत्रह: 17, अठारह: 18, उन्नीस: 19,
  बीस: 20, तीस: 30, चालीस: 40, पचास: 50, साठ: 60, सत्तर: 70, अस्सी: 80,
  नब्बे: 90, सौ: 100,
};

const NOISE = [
  'quintals', 'quintal', 'quint', 'qtls', 'qtl', 'qts', 'q',
  'క్వింటాళ్లు', 'క్వింటాలు', 'క్వింటాల్',
  'क्विंटल', 'क्विंटल्स',
  'acres', 'acre', 'ఎకరాలు', 'ఎకరం', 'एकड़', 'एकड़े',
  'kg', 'kgs', 'kilo', 'kilos', 'kilogram', 'kilograms',
  'కేజీ', 'కిలోలు', 'किलो', 'किलोग्राम',
  'quintals', 'paddy', 'please', 'about', 'approximately', 'around', 'only', 'just', 'and',
  'దయచేసి', 'సుమారు', 'మాత్రమే', 'కృపచేసి',
  'कृपया', 'लगभग', 'केवल', 'और',
];

function parseDigits(text) {
  const cleaned = text.replace(/[,₹Rs]/g, ' ');
  const m = cleaned.match(/\d+(?:\.\d+)?/);
  return m ? parseFloat(m[0]) : null;
}

function wordsToNumber(words) {
  const tables = [EN_NUM, TE_NUM, HI_NUM];
  let total = 0;
  let pendingTens = 0;
  let scale = 0; // remembers a hundred/other scale word
  let found = false;
  for (const raw of words) {
    const w = raw.toLowerCase().replace(/[.,]/g, '');
    let val = null;
    for (const table of tables) if (w in table) { val = table[w]; break; }
    if (val == null) continue;
    found = true;
    if (val === 100) {
      scale = 100;
      if (pendingTens > 0) { total += pendingTens; pendingTens = 0; }
      if (total === 0) total = scale;
    } else if (val >= 20) {
      if (pendingTens > 0) { total += pendingTens; pendingTens = 0; }
      pendingTens = val;
    } else {
      if (scale && total === scale) { /* keep base */ }
      if (pendingTens > 0) { total += pendingTens + val; pendingTens = 0; }
      else total += (scale && total > 0 ? val : val);
    }
  }
  if (pendingTens > 0) total += pendingTens;
  return found ? total : null;
}

/** Parse a spoken/heard string into a number (or null). */
export function parseSpokenNumber(text) {
  if (!text) return null;
  const digitResult = parseDigits(text);
  if (digitResult != null) return digitResult;
  const tokens = text.split(/\s+/).filter((w) => w && !NOISE.includes(w.toLowerCase()));
  return wordsToNumber(tokens);
}
