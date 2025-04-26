#!/bin/bash
set -e

# 检查管理员权限
check_admin() {
    if ! net session > /dev/null 2>&1; then
        echo "请以管理员身份运行此脚本！"
        exit 1
    fi
}

# 安装 winget 软件包
install_winget_apps() {
    local apps=("$@")
    for app in "${apps[@]}"; do
        echo "安装 $app..."
        if winget install --silent --id "$app"; then
            echo "$app 安装成功."
        else
            local ret_code=$?
            if [ $ret_code -eq 43 ]; then
                echo "$app 已安装，跳过."
            else
                echo "安装 $app 失败，错误代码: $ret_code"
                exit $ret_code
            fi
        fi
    done
}

# 安装 scoop 软件包
install_scoop_apps() {
    local apps=("$@")
    for app in "${apps[@]}"; do
        scoop install "$app"
    done
}

# 获取驱动下载链接
get_nvidia_driver_url() {
    local url="https://gfwsl.geforce.cn/services_toolkit/services/com/nvidia/services/AjaxDriverService.php?func=DriverManualLookup&psid=123&pfid=940&osID=135&languageCode=2052&beta=null&isWHQL=0&dltype=-1&dch=1&upCRD=null&qnf=0&sort1=1&numberOfResults=10"
    local json
    json=$(curl -sL "$url")
    if [ -z "$json" ]; then
        echo "无法获取API返回的数据！"
        exit 1
    fi

    local download_url
    download_url=$(echo "$json" | jq -r '.IDS[] | select(.downloadInfo.Name | contains("Game%20Ready")) | .downloadInfo.DownloadURL' | head -n 1)
    if [ -z "$download_url" ]; then
        echo "无法解析到驱动下载链接，请检查 API 返回数据。"
        exit 1
    fi

    echo "$download_url"
}

# 下载驱动
install_nvidia_driver() {
    local download_url=$1
    local download_dir="$HOME/Downloads/drivers"
    local installer_path="$download_dir/$(basename "$download_url")"
    
    echo "下载驱动到: $installer_path"
    curl -C - -L -o "$installer_path" "$download_url"
    if [ $? -ne 0 ]; then
        echo "驱动下载失败！"
        exit 1
    fi

    echo "驱动下载完成，准备安装..."
    powershell -Command "Start-Process '$installer_path'"
}

# 安装 Scoop
install_scoop() {
    if ! command -v scoop &> /dev/null; then
        echo "Scoop 未安装，正在安装..."
        pwsh -Command "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; iwr -useb get.scoop.sh | iex"
    fi
    echo "添加 Scoop bucket..."
    scoop bucket add nerd-fonts
    scoop bucket add extras
    scoop bucket add mine https://github.com/Initsnow/MyScoopBucket
}

# 安装软件
install_software() {
    local winget_apps=("Microsoft.PowerShell" "Nushell.Nushell" "Microsoft.VisualStudioCode" "Sandboxie.Plus" "Zen-Team.Zen-Browser" "Obsidian.Obsidian" "LocalSend.LocalSend" "kangfenmao.CherryStudio" "Valve.Steam" "voidtools.Everything" "Zen-Team.Zen-Browser" "OpenJS.NodeJS.LTS" "Cockos.REAPER" "ShareX.ShareX")
    local scoop_apps=("yazi" "ripgrep" "omenmon" "disable-ctrl-space" "carapace-bin" "git" "helix" "http-downloader" "JetBrainsMono-NF" "jq" "lxgwneoxihei" "lxgwneozhisong" "lxgwwenkaiscreen" "maple-mono-nf-cn" "rclone" "scoop-search" "starship" "syncthing")

    echo "通过 winget 安装软件..."
    install_winget_apps "${winget_apps[@]}"

    echo "通过 scoop 安装软件..."
    install_scoop_apps "${scoop_apps[@]}"
}

restore_classic_right-click_context_menu() {
    reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" -f
    taskkill -F -IM explorer.exe
    explorer.exe &    
}

check_and_convert_to_utf8() {
    local file="$1"

    if [ ! -f "$file" ]; then
        echo "错误：文件 '$file' 不存在。"
        return 1
    fi

    # 使用 file 命令检测文件编码
    # `-b` 选项不显示文件名
    # `--mime-encoding` 选项只显示编码
    encoding=$(file -b --mime-encoding "$file")

    if [ "$encoding" == "utf-8" ] || [ "$encoding" == "us-ascii" ]; then
        # 如果是 UTF-8 或 ASCII (ASCII 是 UTF-8 的子集)，则认为已经是 UTF-8
        echo "文件 '$file' 已经是 UTF-8 编码。"
    else
        # 如果不是 UTF-8，尝试使用 iconv 转换为 UTF-8
        echo "文件 '$file' 的编码是 '$encoding'，尝试转换为 UTF-8。"
        
        # 创建一个临时文件用于存储转换结果
        temp_file=$(mktemp)

        # 使用 iconv 进行转换
        # `-f` 指定源编码，`-t` 指定目标编码
        if iconv -f "$encoding" -t utf-8 "$file" > "$temp_file"; then
            # 转换成功，替换原文件
            mv "$temp_file" "$file"
            echo "文件 '$file' 已成功转换为 UTF-8 编码。"
        else
            # 转换失败
            echo "错误：无法将文件 '$file' 从 '$encoding' 转换为 UTF-8。"
            rm "$temp_file" # 删除临时文件
            return 1
        fi
    fi
    return 0
}

addScheduledTasks() {
    echo "处理计划任务..."
    for xml_file in ScheduledTasks/*.xml; do
        echo "处理文件：${xml_file}"
        check_and_convert_to_utf8 "$xml_file"
        local temp_file=$(mktemp --suffix=.xml)
        sed "s/ComputerName/${COMPUTERNAME}/g; s/UserName/${USERNAME}/g" "$xml_file" > "$temp_file"
        task_name=$(basename "${xml_file}" .xml)
        echo "导入 $(cygpath -w "$temp_file")"
        SCHTASKS -CREATE -XML "$(cygpath -w "$temp_file")" -TN "$task_name"
        rm "$temp_file"
    done
}

uninstallApps() {
    local apps=("Microsoft.DevHome" "MSIX\Microsoft.XboxGamingOverlay_7.225.4081.0_x64__8wekyb3d8bbwe" "MSIX\Microsoft.YourPhone_0.24012.105.0_x64__8wekyb3d8bbwe" "MicrosoftWindows.CrossDevice_0.25032.52.0_x64__cw5n1h2txyewy")
    for app in "${apps[@]}"; do
        winget uninstall "$app"
    done
}

# 主流程
main() {
    # 检查是否以管理员身份运行
    # check_admin

    # 安装 scoop 并配置环境
    install_scoop
    
    # 安装软件
    install_software

    # 创建下载目录
    mkdir -p "$HOME/Downloads/drivers"
    
    # 获取并下载 NVIDIA 驱动
    DRIVER_URL=$(get_nvidia_driver_url)
    install_nvidia_driver "$DRIVER_URL"

    # 执行 debloat 脚本
    echo "正在执行 debloat 脚本..."
    pwsh -Command "Start-Process pwsh -ArgumentList '-NoExit','-Command','& ([scriptblock]::Create((irm \"https://debloat.raphi.re/\")))' -Verb RunAs"

    # 卸载一些自带软件
    uninstallApps

    # 添加计划任务
    addScheduledTasks

    # 右键菜单恢复为win10
    restore_classic_right-click_context_menu
    
    # 设置 yazi 环境变量
    setx YAZI_FILE_ONE "C:\Users\\$USERNAME\scoop\apps\git\current\usr\bin\file.exe"

    # 使用uv安装python
    uv python install
    

    echo "所有操作完成！"
}

