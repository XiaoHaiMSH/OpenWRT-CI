# OpenWRT-CI

源码：

https://github.com/coolsnowwolf/lede.git

# 编译设备

京东云亚瑟（JDCloud AX1800 Pro / RE-SS-01）：`jdcloud_re-ss-01`

Link NN6000 v2：`link_nn6000-v2`

# 固件简要说明

固件每天早上5点自动编译，基于 lede 的 qualcommax/ipq60xx。

固件内置配套 opkg 软件源：kmod 源包含全部内核模块，插件源包含 `Config/PACKAGES.txt` 里的插件，随固件同 commit 发布到 Cloudflare Pages。

软件源域名在 `LEDE-BUILD.yml` 的 `WRT_FEED_HOST` 修改（Pages 项目名取域名第一段，如 `lede-feed.pages.dev` 对应项目 `lede-feed`）；发布前需在 Cloudflare Pages 建好同名项目，并配置 `CLOUDFLARE_ACCOUNT_ID`、`CLOUDFLARE_API_TOKEN` 两个 secrets。

固件信息里的时间为编译开始的时间，方便核对上游源码提交时间。

# 目录简要说明

workflows——自定义CI配置

Scripts——自定义脚本

Config——自定义配置
