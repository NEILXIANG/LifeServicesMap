// 构建期城市配置（cities/<city>/city.json），由 build.py 注入。SP 是 localStorage 键前缀：
// Kamloops 保持 'kamloops'，现有用户的收藏、语言、任务进度不受影响。
const CITY_META=/*__CITY_META__*/;
const SP=CITY_META.storagePrefix;
/*__CITY_DATA__*/
