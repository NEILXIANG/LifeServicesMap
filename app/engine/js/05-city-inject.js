// 构建期城市配置（cities/<city>/city.json），由 build.py 注入。SP 是 localStorage 键前缀：
// Kamloops 保持 'kamloops'，现有用户的收藏、语言、任务进度不受影响。
const CITY_META=/*__CITY_META__*/;
const SP=CITY_META.storagePrefix;
// 2026-10-05: what a whole province shares — its time zone and the guide's province chapter (health card,
// licence, tenancy…) — comes from provinces/<province>/, injected by build.py. The engine holds no BC facts,
// so a city in another province only needs its own provinces/<code>/ (lesson L-040). A city may still
// override any text in its data.js, which runs after this.
const PROVINCE=/*__PROVINCE__*/;
Object.keys(PROVINCE.guide||{}).forEach(l=>{if(UI[l])UI[l].guideProv=PROVINCE.guide[l];});
/*__CITY_DATA__*/
