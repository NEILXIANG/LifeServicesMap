# vendor/

build.py 把这些库内联进产物，地图在没有网络时也能显示。文件是 cdnjs 上对应版本的 `.min` 原样拷贝
（2026-10-03 逐字节核对过与线上页面内联的版本一致），入库是为了构建可复现、不依赖 npm。

- leaflet-1.9.4/leaflet.css, leaflet.js ← cdnjs leaflet/1.9.4/leaflet.min.{css,js}
- leaflet.markercluster-1.5.3/leaflet.markercluster.js ← cdnjs leaflet.markercluster/1.5.3/leaflet.markercluster.min.js

升级版本：换文件、改目录名，同时改 build.py 和 src/engine.html 里的 CDN 地址。
