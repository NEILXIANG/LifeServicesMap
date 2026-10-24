// crisis.js — 危机识别：指南的规则（逐字照抄引擎，见 build.py）+ 工作人员的第三人称说法。
//
// 2026-10-23：指南的规则是给新移民自己用的，写的是第一人称（"打我""hits me""je veux mourir"）。
// 助手的用户是 KIS 工作人员，替客户提问时用第三人称——"她丈夫打她"在指南规则里不命中，
// 会被当成普通问题发给 AI。这里补上第三人称的说法；指南的规则不改（它的用户不这样说）。

import { isCrisis as guideCrisis } from '../build/crisis.js';

const STAFF_RE = new RegExp([
  // 中文：打/虐待/威胁 + 她/他/孩子，想死/自杀 的第三人称
  '(打|揍|殴打|虐待|威胁|跟踪|伤害|强奸|侵犯)(她|他|孩子|小孩|女儿|儿子|太太|妻子|老婆)',
  '(她|他)(想|要)(死|自杀|结束生命)', '(她|他)不安全', '(她|他)(在家|回家)(很)?(害怕|不安全)',
  // English third person
  '\\b(hits|hit|beats|beat|hurts|hurt|chokes|choked|abuses|abused|threatens|threatened|rapes|raped|stalks|stalking) (her|him|them|the (kids?|children|child|baby))\\b',
  '\\b(she|he|they|client)( (is|are|was))? (wants?|wanted|trying|tried|going|plans?) to (die|kill (herself|himself|themselves)|end (her|his|their) life)\\b',
  '\\bkill (herself|himself|themselves)\\b', '\\b(she|he|they) (is|are|feels?) (not safe|unsafe|in danger)\\b',
  // français / español
  '\\b(la|le) (frappe|bat|menace)\\b', '\\bveut mourir\\b', '\\bse suicider\\b',
  '\\b(la|lo) (golpea|pega|amenaza)\\b', '\\bquiere morir\\b', '\\bsuicidarse\\b',
  // 한국어 / 日本語
  '(그녀|그|아이)(를|가)? ?(때|폭행|학대)', '죽고 싶어(해|한다)', '(彼女|彼|子ども|子供)(を|に|が)?(殴|叩|虐待|脅)', '死にたい(と|って)',
].join('|'), 'i');

export function isCrisis(q) {
  return guideCrisis(q) || (!!q && STAFF_RE.test(String(q)));
}
