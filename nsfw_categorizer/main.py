import os
import shutil
from nsfwpy import NSFW

# --- 1. 配置区域 ---

# 需要递归扫描的源文件夹列表
SOURCE_FOLDERS = [
    r"C:\Users\Initsnow\Downloads\cos",
]
# 输出文件夹
DESTINATION_FOLDER = r"C:\Users\Initsnow\Documents\NSFW_tmp\Pics"

# NSFW 分数阈值
PORN_THRESHOLD = 0.7

# --- 2. 主逻辑：扫描并移动符合条件的文件 ---
if __name__ == "__main__":
    # 确保唯一的目标文件夹存在
    os.makedirs(DESTINATION_FOLDER, exist_ok=True)

    print("第一步：加载 NSFW 模型...")
    try:
        detector = NSFW()
        print("模型加载完成。")
    except Exception as e:
        print(f"错误：加载 NSFW 模型失败: {e}")
        exit()

    print("\n第二步：开始扫描并筛选图片...")
    
    moved_count = 0
    
    # 遍历你在 SOURCE_FOLDERS 中配置的每一个顶层文件夹
    for source_folder in SOURCE_FOLDERS:
        if not os.path.isdir(source_folder):
            print(f"\n--- 警告：跳过不存在的文件夹: {source_folder} ---")
            continue

        print(f"\n--- 正在递归扫描: {source_folder} ---")
        
        # 使用 os.walk() 进行递归遍历
        for dirpath, _, filenames in os.walk(source_folder):
            for filename in filenames:
                source_path = os.path.join(dirpath, filename)
                
                # 确保是支持的图片格式
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    continue

                print(f"\n  正在检查: {source_path}")
                
                try:
                    predictions = detector.predict_image(source_path)
                    
                    if predictions is None:
                        print(f"    -> 无法预测，可能文件已损坏或格式不受支持。")
                        continue

                    porn_value = predictions.get('porn', 0.0)
                    
                    try:
                        porn_score = float(porn_value)
                    except (ValueError, TypeError):
                        print(f"    -> 警告：'porn' 分数 '{porn_value}' 无法转换为数字，跳过。")
                        continue
                    
                    print(f"    -> Porn 分数: {porn_score:.4f}")
                    
                    # 如果分数超过阈值，则移动到唯一的指定文件夹
                    if porn_score > PORN_THRESHOLD:
                        destination_path = os.path.join(DESTINATION_FOLDER, filename)
                        
                        if os.path.exists(destination_path):
                            print(f"    -> 目标文件夹已存在同名文件，跳过移动。")
                        else:
                            shutil.move(source_path, destination_path)
                            print(f"    -> 符合条件，已移动到 '{DESTINATION_FOLDER}'")
                            moved_count += 1
                    else:
                        print(f"    -> 分数未达标。")

                except Exception as e:
                    print(f"    -> 处理文件时发生未知错误: {e}")
                    
    # --- 3. 最终总结 ---
    print("\n\n--- 所有处理完成！---")
    print(f"总共移动了 {moved_count} 个文件到 '{DESTINATION_FOLDER}'")