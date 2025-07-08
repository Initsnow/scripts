# -*- coding: utf-8 -*-
import os
import re
import shutil
import argparse
from pathlib import Path

def find_file_in_vault(filename, vault_path):
    """
    Recursively searches for a file within the Obsidian vault.
    
    Args:
        filename (str): The name of the file to search for.
        vault_path (str): The root path of the Obsidian vault.

    Returns:
        Path object or None: The full path to the file if found, otherwise None.
    """
    for root, _, files in os.walk(vault_path):
        # 使用 os.path.normcase 进行不区分大小写的比较，以更好地兼容 Windows 系统
        if os.path.normcase(filename) in [os.path.normcase(f) for f in files]:
            return Path(root) / filename
    return None

def process_markdown_file(markdown_path, vault_path, attachments_folder="attachments"):
    """
    Processes a single Markdown file to move its attachments and update links.

    Args:
        markdown_path (Path): The path to the Markdown file.
        vault_path (Path): The root path of the Obsidian vault.
        attachments_folder (str): The name of the folder to move attachments to.
    """
    if not markdown_path.is_file():
        print(f"❌ 错误：文件不存在 -> {markdown_path}")
        return

    print(f"📄 正在处理文件: {markdown_path.name}")

    # 1. 定义路径
    markdown_dir = markdown_path.parent
    dest_dir = markdown_dir / attachments_folder

    # 2. 读取 Markdown 文件内容
    try:
        content = markdown_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ 读取文件时出错 {markdown_path}: {e}")
        return

    # 3. 查找所有 [[...]] 格式的链接中的文件名部分
    # 这个正则表达式可以正确提取文件名，无论链接是否带别名或指向标题
    wikilinks = re.findall(r'!*\[\[([^|\]#]+)', content)
    
    if not wikilinks:
        print("🔵 未在该文件中找到符合条件的 [[...]] 链接。")
        return

    print(f"🔍 找到 {len(set(wikilinks))} 个唯一链接: {set(wikilinks)}")

    updated_content = content
    files_moved_count = 0
    folder_created = False # 用于跟踪文件夹是否已创建的标志

    # 4. 遍历并处理每个链接
    for link_name in set(wikilinks):
        link_name = link_name.strip() # 去除可能存在的前后空格

        # 检查链接是否已经指向附件文件夹
        if link_name.startswith(attachments_folder + '/') or link_name.startswith(attachments_folder + '\\'):
            print(f"✅ 链接 '{link_name}' 已在目标文件夹中，跳过。")
            continue
            
        # 检查这是否是一个指向其他 Markdown 文档的链接 (即使没有 .md 后缀)
        potential_md_file = find_file_in_vault(f"{link_name}.md", str(vault_path))
        if potential_md_file:
            print(f"⚪️ 链接 '{link_name}' 指向一个 Markdown 文档 ({potential_md_file.name})，跳过。")
            continue

        # 在整个库中查找源文件
        source_path = find_file_in_vault(link_name, str(vault_path))

        if not source_path:
            print(f"⚠️  警告：在库中找不到文件 '{link_name}'，跳过。")
            continue

        # 检查文件是否已在正确的位置
        if source_path.parent == dest_dir:
            print(f"✅ 文件 '{link_name}' 已在目标位置，跳过。")
            continue

        # 定义新路径
        dest_path = dest_dir / source_path.name
        
        try:
            # 只有在确定要移动第一个文件时才创建附件文件夹
            if not folder_created:
                print(f"📁 检测到需要移动的附件，创建文件夹: {dest_dir}")
                dest_dir.mkdir(exist_ok=True)
                folder_created = True

            print(f"🚀 正在移动: '{source_path}' -> '{dest_path}'")
            shutil.move(source_path, dest_path)
            files_moved_count += 1

            # --- 更新链接的核心逻辑 ---
            escaped_link = re.escape(link_name)
            pattern = re.compile(r'(!?\[\[)(' + escaped_link + r')(?=[|\]#])')
            replacement_string = rf'\g<1>{attachments_folder}/\g<2>'
            updated_content = pattern.sub(replacement_string, updated_content)
            print(f"✍️  已更新链接，将 '{link_name}' 指向 '{attachments_folder}' 文件夹。")

        except Exception as e:
            print(f"❌ 移动文件 '{source_path}' 时出错: {e}")

    # 5. 将更新后的内容写回文件
    if content != updated_content:
        try:
            markdown_path.write_text(updated_content, encoding='utf-8')
            print(f"💾 成功将更新后的内容保存到 {markdown_path.name}")
        except Exception as e:
            print(f"❌ 保存文件 {markdown_path.name} 时出错: {e}")
    
    if files_moved_count > 0:
        print(f"✨ 处理完成！共移动了 {files_moved_count} 个文件。")
    else:
        print("✨ 处理完成！没有文件被移动。")


def main():
    """
    主函数，用于解析命令行参数并启动处理流程。
    """
    parser = argparse.ArgumentParser(
        description="整理 Obsidian Markdown 文件中的附件，将其移动到指定文件夹并更新链接。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "markdown_file", 
        type=str,
        help="要处理的 Markdown 文件的路径。"
    )
    parser.add_argument(
        "-v", "--vault", 
        type=str, 
        required=True,
        help="您的 Obsidian 库 (Vault) 的根目录路径。"
    )
    parser.add_argument(
        "-d", "--dest", 
        type=str, 
        default="attachments",
        help="用于存放附件的文件夹名称。\n"
             "这个文件夹将被创建在 Markdown 文件所在的目录中。\n"
             "默认为: 'attachments'。"
    )

    args = parser.parse_args()

    markdown_path = Path(args.markdown_file).resolve()
    vault_path = Path(args.vault).resolve()

    if not vault_path.is_dir():
        print(f"❌ 错误：指定的库路径不是一个有效的目录 -> {vault_path}")
        return

    process_markdown_file(markdown_path, vault_path, args.dest)

if __name__ == "__main__":
    main()
