import os
import csv
from pathlib import Path
from collections import defaultdict

def check_trim_image_csv_consistency(trim_base_dir, csv_base_dir):
    """
    trim_imageファイル数とCSVファイルの行数を比較して一致性をチェックする
    
    Args:
        trim_base_dir (str): trim_imageが格納されているベースディレクトリのパス
        csv_base_dir (str): CSVファイルが格納されているベースディレクトリのパス
    """
    # ディレクトリの存在確認
    if not os.path.exists(trim_base_dir):
        print(f"エラー: trim_imageディレクトリ '{trim_base_dir}' が存在しません。")
        return
    
    if not os.path.exists(csv_base_dir):
        print(f"エラー: CSVディレクトリ '{csv_base_dir}' が存在しません。")
        return
    
    if not os.path.isdir(trim_base_dir):
        print(f"エラー: '{trim_base_dir}' はディレクトリではありません。")
        return
    
    if not os.path.isdir(csv_base_dir):
        print(f"エラー: '{csv_base_dir}' はディレクトリではありません。")
        return
    
    # trim_imageディレクトリから日付ディレクトリを検索（8桁の数字のディレクトリ）
    trim_date_directories = []
    for item in os.listdir(trim_base_dir):
        item_path = os.path.join(trim_base_dir, item)
        if os.path.isdir(item_path) and item.isdigit() and len(item) == 8:
            trim_date_directories.append(item)
    
    if not trim_date_directories:
        print(f"ディレクトリ '{trim_base_dir}' に8桁の日付ディレクトリが見つかりません。")
        return
    
    # CSVディレクトリからCSVファイルを検索し、ファイル名から8桁の日付を抽出
    csv_date_files = {}
    for item in os.listdir(csv_base_dir):
        item_path = os.path.join(csv_base_dir, item)
        if os.path.isfile(item_path) and item.lower().endswith('.csv'):
            # CSVファイル名から8桁の数字を抽出
            import re
            date_match = re.search(r'(\d{8})', item)
            if date_match:
                date_str = date_match.group(1)
                if date_str not in csv_date_files:
                    csv_date_files[date_str] = []
                csv_date_files[date_str].append(item)
    
    if not csv_date_files:
        print(f"ディレクトリ '{csv_base_dir}' に日付を含むCSVファイルが見つかりません。")
        return
    
    # 共通の日付を取得
    common_dates = sorted(set(trim_date_directories) & set(csv_date_files.keys()))
    
    if not common_dates:
        print("共通の日付ディレクトリが見つかりません。")
        return
    
    print(f"trim_imageとCSVの一致性をチェックします...\n")
    print(f"trim_imageベース: {trim_base_dir}")
    print(f"CSVベース: {csv_base_dir}")
    print(f"共通日付: {len(common_dates)} 個\n")
    
    total_trim_images = 0
    total_csv_lines = 0
    date_summary = defaultdict(dict)
    
    # 各共通日付ディレクトリを処理
    for date_dir in common_dates:
        print(f"=== {date_dir} ===")
        
        # trim_imageのパス
        trim_date_path = os.path.join(trim_base_dir, date_dir, "affine_data")
        
        if not os.path.exists(trim_date_path):
            print("  trim_image affine_dataフォルダが見つかりません")
            continue
        
        # affine_data内のtrim_imageディレクトリを検索
        trim_image_path = os.path.join(trim_date_path, "trim_image")
        
        if not os.path.exists(trim_image_path):
            print("  trim_imageディレクトリが見つかりません")
            continue
        
        if not os.path.isdir(trim_image_path):
            print("  trim_imageはディレクトリではありません")
            continue
        
        # trim_imageディレクトリ内のnpyファイル数をカウント
        try:
            trim_files = [f for f in os.listdir(trim_image_path) if f.endswith('.npy') and os.path.isfile(os.path.join(trim_image_path, f))]
            trim_count = len(trim_files)
        except Exception as e:
            print(f"  trim_imageディレクトリの読み込みエラー: {e}")
            continue
        
        # 該当日付のCSVファイルを取得
        csv_files = csv_date_files.get(date_dir, [])
        
        if not csv_files:
            print(f"  日付 {date_dir} に対応するCSVファイルが見つかりません")
            continue
        
        # CSVファイルの行数をカウント
        csv_line_count = 0
        if csv_files:
            # 最初のCSVファイルの行数をカウント（日付ごとに1つのCSVファイルがある想定）
            csv_path = os.path.join(csv_base_dir, csv_files[0])
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    csv_line_count = sum(1 for line in f)
            except UnicodeDecodeError:
                try:
                    with open(csv_path, 'r', encoding='shift_jis') as f:
                        csv_line_count = sum(1 for line in f)
                except Exception as e:
                    csv_line_count = 0
        csv_line_count = csv_line_count - 1
        # パス情報を表示
        print(f"  trim_imageディレクトリ: {trim_image_path}")
        print(f"  CSVファイル: {csv_path}")
        print(f"  trim_image: {trim_count} ファイル")
        print(f"  CSV行数: {csv_line_count} 行")
        
        # 一致性をチェック
        status = "✓ 一致" if trim_count == csv_line_count else "✗ 不一致"
        print(f"  状態: {status}")
        
        total_trim_images += trim_count
        total_csv_lines += csv_line_count
        
        date_summary[date_dir] = {
            'trim_images': trim_count,
            'csv_lines': csv_line_count,
            'consistent': trim_count == csv_line_count
        }
        print()
    
    # 全体のサマリーを表示
    print("=" * 60)
    print("全体サマリー:")
    print("-" * 30)
    
    for date_dir in sorted(date_summary.keys()):
        summary = date_summary[date_dir]
        status = "✓ 一致" if summary['consistent'] else "✗ 不一致"
        print(f"{date_dir}: trim_image {summary['trim_images']:,} ファイル, CSV {summary['csv_lines']:,} 行 - {status}")
    
    overall_consistent = total_trim_images == total_csv_lines
    print(f"\n総合計:")
    print(f"  trim_image: {total_trim_images:,} ファイル")
    print(f"  CSV行数: {total_csv_lines:,} 行")
    print(f"  全体状態: {'✓ 一致' if overall_consistent else '✗ 不一致'}")
    print(f"  処理した日付ディレクトリ: {len(common_dates)} 個")

def main():
    """メイン関数"""
    print("trim_image と CSV 行数の一致性チェッカー")
    print("=" * 60)
    
    # 固定のディレクトリパス
    trim_base_directory = r"C:\Users\tyamaguchi\Desktop\smk_system\data\nir_image"
    csv_base_directory = r"C:\Users\tyamaguchi\Desktop\smk_system\data\nir_env\BP"
    
    print(f"trim_imageベースディレクトリ: {trim_base_directory}")
    print(f"CSVベースディレクトリ: {csv_base_directory}")
    
    # 一致性チェック実行
    check_trim_image_csv_consistency(trim_base_directory, csv_base_directory)

if __name__ == "__main__":
    main()
