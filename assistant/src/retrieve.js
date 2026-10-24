// retrieve.js — 从指南的已核实内容里找出和问题相关的办事卡与地点（说明 §8.1 第 1 步）。
//
// 办事卡只有十几张，每次全部交给 AI（用提问的语言 + 英文），不靠检索挑；
// 地点有几百个，按关键词打分挑出最相关的几个，再加上办事卡里点名的地点。
// 分词不依赖任何语言库：拉丁字母按词，中日韩文字按相邻两字（bigram），
// 这样六种语言和 KIS 客户常用的其他语言（只要是拉丁字母或中日韩）都能匹配。

export const LANGS = ['zh', 'en', 'fr', 'es', 'ko', 'ja'];

const CJK = /[぀-ヿ㐀-鿿가-힯豈-﫿]/;
const STOP = new Set(['the', 'and', 'for', 'how', 'what', 'where', 'can', 'do', 'does', 'is', 'are', 'my', 'to', 'in', 'of', 'a', 'an',
  'i', 'me', 'we', 'you', 'it', 'on', 'at', 'with', 'kamloops', 'bc', 'le', 'la', 'les', 'de', 'des', 'du', 'et', 'un', 'une',
  'el', 'los', 'las', 'en', 'y', 'que', 'por', 'para', 'con', 'como', 'comment', 'où', 'est', 'je', 'mon', 'ma']);

export function tokens(text) {
  const out = [];
  const s = String(text || '').toLowerCase().normalize('NFKC');
  for (const w of s.match(/[\p{L}\p{N}]+/gu) || []) {
    if (CJK.test(w)) {
      // 中日韩：连续的汉字/假名/谚文切成两字一组；单字词也保留
      const chars = [...w].filter(c => CJK.test(c));
      if (chars.length === 1) out.push(chars[0]);
      for (let i = 0; i + 1 < chars.length; i++) out.push(chars[i] + chars[i + 1]);
      const latin = w.replace(new RegExp(CJK.source, 'g'), ' ').match(/[a-z0-9]{2,}/g);
      if (latin) out.push(...latin.filter(x => !STOP.has(x)));
    } else if (w.length >= 2 && !STOP.has(w)) {
      out.push(w);
      // 很粗的词干：去掉英法西语常见复数/词尾，让 school / schools、clínica / clínicas 能对上
      if (w.length > 4 && /s$/.test(w)) out.push(w.slice(0, -1));
    }
  }
  return out;
}

function placeText(p) {
  return [p.n, p.a, ...Object.values(p.cat || {}), ...Object.values(p.note || {}), ...(p.alias || [])].join(' ');
}

function taskText(t) {
  const parts = [...(t.alias || [])];
  for (const k of ['t', 'q', 'why', 'cost', 'bring', 'note', 'help']) if (t[k]) parts.push(...Object.values(t[k]));
  for (const s of t.steps || []) parts.push(...Object.values(s));
  return parts.join(' ');
}

// BM25（k1=1.2, b=0.75）。索引在 Worker 启动时建一次。
export function buildIndex(docs) {
  const rows = docs.map(d => {
    const tf = new Map();
    const toks = tokens(d.kind === 'task' ? taskText(d) : placeText(d));
    for (const t of toks) tf.set(t, (tf.get(t) || 0) + 1);
    // 名称、分类名、别名再计一次：问"图书馆"时，名字里就有 Library 的地点应排在前面
    const strong = d.kind === 'place' ? [d.n, ...Object.values(d.cat || {}), ...(d.alias || [])] : [...(d.alias || []), ...Object.values(d.t || {})];
    for (const t of tokens(strong.join(' '))) tf.set(t, (tf.get(t) || 0) + 2);
    return { d, tf, len: toks.length || 1 };
  });
  const df = new Map();
  for (const r of rows) for (const t of r.tf.keys()) df.set(t, (df.get(t) || 0) + 1);
  const avg = rows.reduce((a, r) => a + r.len, 0) / (rows.length || 1);
  return { rows, df, avg, N: rows.length };
}

export function search(index, query, { kind, limit = 8 } = {}) {
  const q = [...new Set(tokens(query))];
  const scored = [];
  for (const r of index.rows) {
    if (kind && r.d.kind !== kind) continue;
    let s = 0;
    for (const t of q) {
      const f = r.tf.get(t);
      if (!f) continue;
      const idf = Math.log(1 + (index.N - index.df.get(t) + 0.5) / (index.df.get(t) + 0.5));
      s += idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * r.len / index.avg));
    }
    if (s > 0) scored.push({ d: r.d, s });
  }
  scored.sort((a, b) => b.s - a.s);
  return scored.slice(0, limit);
}

// 给 AI 的内容：全部办事卡 + 相关地点。返回 { tasks, places }，都是知识文件里的原始记录。
export function retrieve(know, index, query, { placeLimit = 8 } = {}) {
  const tasks = know.docs.filter(d => d.kind === 'task');
  const byId = new Map(know.docs.map(d => [d.id, d]));
  const hits = search(index, query, { kind: 'place', limit: placeLimit });
  const places = hits.map(h => h.d);
  // 问题最相关的两张办事卡点名的地点（如 SIN 卡的 Service Canada）也一起给
  for (const h of search(index, query, { kind: 'task', limit: 2 })) {
    const p = h.d.place && byId.get('place:' + h.d.place);
    if (p && !places.includes(p)) places.push(p);
  }
  return { tasks, places, topTasks: search(index, query, { kind: 'task', limit: 3 }).map(h => h.d) };
}
