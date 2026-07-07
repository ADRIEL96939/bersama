// Bersama, in the browser.
// A small TF-IDF retriever plus grounded-answer logic that runs entirely
// client-side, so the demo can live on GitHub Pages with no server. It mirrors
// the Python pipeline: retrieve in the worker's language, answer from official
// passages, cite them, and decline when nothing is relevant.

const MIN_RELEVANCE = 0.12;
const TOP_K = 3;

const STOPWORDS = {
  en: new Set(("a an the and or but if while of to in on at by for with about "
    + "is are was were be been being do does did have has had i you he she it we "
    + "they me my your his her its our their this that these those what which who "
    + "whom how when where why can could should would will shall may might must "
    + "not no nor as so than then there here just only very more most some any "
    + "each from into out up down over under again further can't dont do i'm").split(/\s+/)),
  id: new Set(("saya aku kamu anda dia kita kami mereka ini itu yang di ke dari "
    + "untuk pada dengan dan atau tapi tetapi karena jika kalau agar supaya apa "
    + "apakah bagaimana berapa siapa kapan mana dimana mengapa kenapa adalah akan "
    + "sudah telah sedang bisa bisakah dapat harus boleh bolehkah tidak bukan ada "
    + "adakah jadi juga saja lagi masih sangat lebih paling oleh sebagai dalam atas "
    + "bawah saat ketika setelah sebelum hingga sampai antara para nya pun per bagi "
    + "tentang seperti yaitu maupun serta hal cara melakukan membuat yg ya punya banyak").split(/\s+/)),
  vi: new Set(("tôi bạn anh chị em họ chúng ta mình nó của và hoặc nhưng vì nếu khi "
    + "để cho với từ đến tại trong ngoài trên dưới về theo bằng là có không được sẽ "
    + "đã đang bị phải cần nên thì mà này đó kia các những một gì ai sao nào đâu bao "
    + "nhiêu thế rất quá hơn cũng vẫn còn chỉ đều ra vào lên xuống hay nhé ạ ừ vâng ở "
    + "cùng rồi lúc việc người hãy đi").split(/\s+/)),
};

const STRINGS = {
  en: {
    intro: "Here is what the official sources say:",
    sources: "Sources",
    noAnswer: "I do not have verified information about that yet. For help, you can call the free 1955 hotline (dial 1955), which is open 24 hours and has staff who speak several languages.",
  },
  id: {
    intro: "Berikut yang dikatakan oleh sumber resmi:",
    sources: "Sumber",
    noAnswer: "Saya belum memiliki informasi yang terverifikasi tentang itu. Untuk bantuan, Anda bisa menelepon hotline gratis 1955 (tekan 1955), yang buka 24 jam dan memiliki staf yang berbicara beberapa bahasa.",
  },
  vi: {
    intro: "Đây là những gì các nguồn chính thức cho biết:",
    sources: "Nguồn",
    noAnswer: "Tôi chưa có thông tin đã được xác minh về điều đó. Để được giúp đỡ, bạn có thể gọi đường dây nóng miễn phí 1955 (bấm 1955), mở cửa 24 giờ và có nhân viên nói được nhiều thứ tiếng.",
  },
};

function tokenize(text, lang) {
  const stop = STOPWORDS[lang] || STOPWORDS.en;
  const raw = (text.toLowerCase().match(/[\p{L}\p{N}]+/gu) || [])
    .filter((t) => t.length >= 2 && !stop.has(t));
  // unigrams + bigrams (matches the Python ngram_range=(1,2))
  const grams = raw.slice();
  for (let i = 0; i < raw.length - 1; i++) grams.push(raw[i] + " " + raw[i + 1]);
  return grams;
}

function indexText(p) {
  return p.topic.replace(/_/g, " ") + ". " + p.text;
}

// Build a per-language TF-IDF index from a list of passages.
export function buildIndex(passages, lang) {
  const docs = passages.map((p) => tokenize(indexText(p), lang));
  const N = docs.length;
  const df = new Map();
  docs.forEach((toks) => {
    new Set(toks).forEach((t) => df.set(t, (df.get(t) || 0) + 1));
  });
  const idf = new Map();
  df.forEach((d, t) => idf.set(t, Math.log((1 + N) / (1 + d)) + 1));

  const vectors = docs.map((toks) => {
    const tf = new Map();
    toks.forEach((t) => tf.set(t, (tf.get(t) || 0) + 1));
    const vec = new Map();
    let norm = 0;
    tf.forEach((c, t) => {
      const w = c * (idf.get(t) || 0);
      vec.set(t, w);
      norm += w * w;
    });
    norm = Math.sqrt(norm) || 1;
    vec.forEach((w, t) => vec.set(t, w / norm));
    return vec;
  });

  return { passages, lang, idf, vectors };
}

function queryVector(query, index) {
  const toks = tokenize(query, index.lang);
  const tf = new Map();
  toks.forEach((t) => tf.set(t, (tf.get(t) || 0) + 1));
  const vec = new Map();
  let norm = 0;
  tf.forEach((c, t) => {
    const idf = index.idf.get(t);
    if (!idf) return; // ignore terms not in the corpus, like scikit-learn
    const w = c * idf;
    vec.set(t, w);
    norm += w * w;
  });
  norm = Math.sqrt(norm) || 1;
  vec.forEach((w, t) => vec.set(t, w / norm));
  return vec;
}

export function retrieve(index, query, k = TOP_K) {
  const q = queryVector(query, index);
  const scored = index.vectors.map((vec, i) => {
    let dot = 0;
    // iterate the smaller map
    const [small, big] = q.size < vec.size ? [q, vec] : [vec, q];
    small.forEach((w, t) => {
      const o = big.get(t);
      if (o) dot += w * o;
    });
    return { passage: index.passages[i], score: dot };
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, k);
}

// Produce a grounded answer object, or a decline, mirroring generation.py.
export function answer(index, query) {
  const lang = index.lang;
  const s = STRINGS[lang] || STRINGS.en;
  const retrieved = retrieve(index, query, TOP_K);
  const relevant = retrieved.filter((r) => r.score >= MIN_RELEVANCE);
  if (relevant.length === 0) {
    return { grounded: false, text: s.noAnswer, sources: [], intro: "", topTopic: null };
  }
  return {
    grounded: true,
    intro: s.intro,
    sourcesLabel: s.sources,
    items: relevant.map((r) => r.passage.text),
    sources: relevant.map((r) => ({ title: r.passage.source_title, url: r.passage.source_url })),
    topTopic: relevant[0].passage.topic,
  };
}

// Employer-transfer form draft (draft only, never submits), localized labels.
const FORM_LABELS = {
  en: { title: "DRAFT - Employer transfer request",
    note: "Please review carefully. This is a draft, not a submitted form.",
    fields: { full_name: "Full name", nationality: "Nationality", arc_number: "ARC number",
      current_employer: "Current employer", job_category: "Job type", reason: "Reason for transfer",
      contact_phone: "Phone" },
    steps: "Next steps: check the current official form and required documents; if anything is unclear, call the free 1955 hotline; have a caseworker or the labor bureau review this before submitting." },
  id: { title: "DRAF - Permohonan pindah majikan",
    note: "Harap periksa dengan teliti. Ini adalah draf, bukan formulir yang sudah dikirim.",
    fields: { full_name: "Nama lengkap", nationality: "Kewarganegaraan", arc_number: "Nomor ARC",
      current_employer: "Majikan saat ini", job_category: "Jenis pekerjaan", reason: "Alasan pindah",
      contact_phone: "Telepon" },
    steps: "Langkah berikutnya: periksa formulir resmi terbaru dan dokumen yang diperlukan; jika ada yang tidak jelas, telepon hotline gratis 1955; minta pendamping atau dinas tenaga kerja meninjau ini sebelum dikirim." },
  vi: { title: "BẢN NHÁP - Đơn xin chuyển chủ",
    note: "Vui lòng xem kỹ. Đây là bản nháp, không phải đơn đã nộp.",
    fields: { full_name: "Họ và tên", nationality: "Quốc tịch", arc_number: "Số ARC",
      current_employer: "Chủ hiện tại", job_category: "Loại công việc", reason: "Lý do chuyển chủ",
      contact_phone: "Điện thoại" },
    steps: "Các bước tiếp theo: kiểm tra đơn chính thức mới nhất và giấy tờ cần thiết; nếu có gì chưa rõ, gọi đường dây nóng miễn phí 1955; nhờ nhân viên hỗ trợ hoặc sở lao động xem lại trước khi nộp." },
};

export function formFields(lang) {
  return FORM_LABELS[lang] || FORM_LABELS.en;
}

export function renderDraft(values, lang) {
  const L = FORM_LABELS[lang] || FORM_LABELS.en;
  const lines = [L.title, "(" + L.note + ")", ""];
  for (const key of Object.keys(L.fields)) {
    lines.push(L.fields[key] + ": " + (values[key] || ""));
  }
  lines.push("", L.steps);
  return lines.join("\n");
}
