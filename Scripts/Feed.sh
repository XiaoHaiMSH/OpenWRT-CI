#!/bin/bash
# SPDX-License-Identifier: MIT
# 软件源脚本，在 ./wrt/ 目录下运行：
#   Feed.sh apply    把 Config/PACKAGES.txt 里的包写成 =m（只编译，不进固件）
#   Feed.sh check    defconfig 之后检查每个包是否真的是 =m
#   Feed.sh collect  编译完成后收集全部 apk，生成 packages.adb 索引
#   Feed.sh domain   输出软件源域名；project 输出 Pages 项目名（域名去掉 .pages.dev）

#====================================================
#软件源域名：在下面引号里填 Cloudflare Pages 域名，不带 https://
#例如 FEED_DOMAIN="my-feed.pages.dev"，留空则不启用软件源
FEED_DOMAIN=""
#====================================================

LIST="$GITHUB_WORKSPACE/Config/PACKAGES.txt"
#Cloudflare Pages 单文件上限 25 MiB
MAX_BYTES=26214400

#读取包名：忽略注释、空行、CRLF，兼容直接粘贴 CONFIG_PACKAGE_xxx=m 的写法
READ_LIST() {
	[ -f "$LIST" ] || return 0
	sed -E 's/\r$//; s/#.*$//; s/^[[:space:]]+//; s/[[:space:]]+$//; s/^CONFIG_PACKAGE_//; s/=.*$//' "$LIST" | grep -v '^$'
}

APPLY() {
	local COUNT=0 PKG RE

	while read -r PKG; do
		#先清掉 .config 里该包的旧设置，以 PACKAGES.txt 为准
		RE=$(printf '%s' "$PKG" | sed 's/[][\\.*^$/]/\\&/g')
		sed -i "/^CONFIG_PACKAGE_${RE}=/d; /^# CONFIG_PACKAGE_${RE} is not set/d" ./.config
		echo "CONFIG_PACKAGE_${PKG}=m" >> ./.config
		COUNT=$((COUNT + 1))
	done < <(READ_LIST)

	echo "PACKAGES.txt: $COUNT packages set to =m"
}

CHECK() {
	local OK=0 PKG VAL

	while read -r PKG; do
		VAL=$(awk -F= -v k="CONFIG_PACKAGE_$PKG" '$1 == k { print $2; exit }' ./.config)
		case "$VAL" in
			m) OK=$((OK + 1)) ;;
			y) echo "::warning::$PKG 被固件里的其他包依赖，已变成 =y，会进固件" ;;
			*) echo "::warning::$PKG 没有生效，包不存在或名称写错" ;;
		esac
	done < <(READ_LIST)

	echo "PACKAGES.txt: $OK packages confirmed as =m"
}

COLLECT() {
	local OUT="${FEED_OUT:-$GITHUB_WORKSPACE/feed}/$WRT_CONFIG"
	local APK="$PWD/staging_dir/host/bin/apk"
	local TMP FILE

	rm -rf "$OUT" && mkdir -p "$OUT"

	#用户态包在 bin/packages，内核模块等在 bin/targets/*/*/packages
	find ./bin/packages ./bin/targets -type f -name "*.apk" -exec cp -f {} "$OUT/" \;

	if ! ls "$OUT"/*.apk > /dev/null 2>&1; then
		echo "::error::没有找到任何 apk 文件，这个脚本只支持 apk 软件源"
		exit 1
	fi

	#超过 Pages 单文件上限的包先剔除，再建索引，这样索引里不会出现装不上的包
	while read -r FILE; do
		echo "::warning::$(basename "$FILE") 超过 25 MiB，未放入软件源"
		rm -f "$FILE"
	done < <(find "$OUT" -maxdepth 1 -type f -name "*.apk" -size +${MAX_BYTES}c)

	[ -x "$APK" ] || { echo "::error::找不到 $APK"; exit 1; }

	TMP=$(mktemp -d)
	cd "$OUT" || exit 1
	#--root 指向空目录，避免读取宿主机的 apk 配置；失败时去掉再试一次
	if ! "$APK" mkndx --allow-untrusted --root "$TMP" -o packages.adb ./*.apk 2> "$TMP/mkndx.log"; then
		cat "$TMP/mkndx.log"
		echo "retry without --root"
		"$APK" mkndx --allow-untrusted -o packages.adb ./*.apk || { echo "::error::生成 packages.adb 失败"; exit 1; }
	fi

	echo "feed: $(ls ./*.apk | wc -l) packages, $(du -sh . | cut -f1), index $(du -h packages.adb | cut -f1)"
}

case "$1" in
	apply) APPLY ;;
	check) CHECK ;;
	collect) COLLECT ;;
	domain) echo "$FEED_DOMAIN" ;;
	project) echo "${FEED_DOMAIN%.pages.dev}" ;;
	*) echo "usage: $0 apply|check|collect|domain|project"; exit 1 ;;
esac
