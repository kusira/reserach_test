import os
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

def parse_trim_image_time(filename):
    """
    trim_imageファイル名から時刻を解析する
    
    Args:
        filename (str): ファイル名 (例: 20241213-073154-781.npy)
    
    Returns:
        tuple: (datetime, milliseconds) 解析された時刻とミリ秒
    """
    # ファイル名から日付と時刻を抽出 (例: 20241213-073154-781.npy)
    match = re.match(r'(\d{8})-(\d{6})-(\d+)\.npy', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        milliseconds = int(match.group(3))
        # 日付と時刻を結合してdatetimeオブジェクトを作成
        datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        base_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        # ミリ秒をマイクロ秒に変換して追加
        time_with_ms = base_time.replace(microsecond=milliseconds * 1000)
        return (time_with_ms, milliseconds)
    return None

def parse_csv_time(time_str):
    """
    CSVの1列目から時刻を解析する
    
    Args:
        time_str (str): 時刻文字列 (例: 2024/12/13 7:31)
    
    Returns:
        datetime: 解析された時刻
    """
    try:
        # 時刻文字列を解析 (例: 2024/12/13 7:31)
        return datetime.strptime(time_str.strip(), "%Y/%m/%d %H:%M")
    except ValueError:
        try:
            # 秒が含まれている場合 (例: 2024/12/13 7:31:00)
            return datetime.strptime(time_str.strip(), "%Y/%m/%d %H:%M:%S")
        except ValueError:
            return None

def check_trim_image_csv_timing(trim_base_dir, csv_base_dir, time_diff_threshold=300, trim_interval_threshold=1, csv_match_required=True):
    """
    trim_imageファイルの時刻とCSVファイルの1列目時刻を比較して、
    一対一対応と時刻差を測定する
    
    Args:
        trim_base_dir (str): trim_imageが格納されているベースディレクトリのパス
        csv_base_dir (str): CSVファイルが格納されているベースディレクトリのパス
        time_diff_threshold (float): 時刻差の警告閾値（秒、デフォルト: 300秒）
        trim_interval_threshold (float): trim_image間隔の警告閾値（秒、デフォルト: 1秒）
        csv_match_required (bool): CSV行一致が必須かどうか（デフォルト: True）
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
    
    print(f"trim_imageとCSVの時刻対応と時刻差を測定します...\n")
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
        
        # trim_imageディレクトリ内のnpyファイルを取得
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
        
        # CSVファイルの1列目から時刻を読み込み
        csv_path = os.path.join(csv_base_dir, csv_files[0])
        csv_times = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                for row in reader:
                    if row and len(row) > 0 and row[0].strip():  # 1列目が存在し、空でない場合
                        csv_time = parse_csv_time(row[0])
                        if csv_time:
                            csv_times.append(csv_time)
        except UnicodeDecodeError:
            try:
                with open(csv_path, 'r', encoding='shift_jis') as f:
                    reader = csv.reader(f)
                    next(reader)  # ヘッダー行をスキップ
                    for row in reader:
                        if row and len(row) > 0 and row[0].strip():  # 1列目が存在し、空でない場合
                            csv_time = parse_csv_time(row[0])
                            if csv_time:
                                csv_times.append(csv_time)
            except Exception as e:
                print(f"  CSVファイルの読み込みエラー: {e}")
                continue
        
        # trim_imageファイルの時刻を解析
        trim_times = []
        for filename in trim_files:
            trim_time_result = parse_trim_image_time(filename)
            if trim_time_result:
                trim_time, milliseconds = trim_time_result
                trim_times.append((filename, trim_time, milliseconds))
        
        # 時刻でソート
        trim_times.sort(key=lambda x: x[1])
        csv_times.sort()
        
        # パス情報を表示
        print(f"  trim_imageディレクトリ: {trim_image_path}")
        print(f"  CSVファイル: {csv_path}")
        print(f"  trim_image: {len(trim_times)} ファイル")
        print(f"  CSV1列目: {len(csv_times)} 行")
        
        # 一対一対応と時刻差を測定
        if len(trim_times) == len(csv_times):
            print(f"  一対一対応: ✓ 一致")
            print(f"  時刻差の詳細:")
            
            total_time_diff = 0
            max_time_diff = 0
            min_time_diff = float('inf')
            
            # セット内の時間差を計算
            set_time_diffs = []
            
            # 警告チェック用のリスト
            warnings = []
            
            for i, ((trim_file, trim_time, milliseconds), csv_time) in enumerate(zip(trim_times, csv_times)):
                time_diff = abs((trim_time - csv_time).total_seconds())
                total_time_diff += time_diff
                max_time_diff = max(max_time_diff, time_diff)
                min_time_diff = min(min_time_diff, time_diff)
                
                # 時刻差の警告チェック
                if time_diff >= time_diff_threshold:
                    warnings.append(f"    時刻差警告: {trim_file} - CSV時刻差 {time_diff:.1f}秒 >= {time_diff_threshold}秒")
                
                print(f"    {i+1:3d}: {trim_file} ({trim_time.strftime('%H:%M:%S.%f')[:-3]}) - CSV ({csv_time.strftime('%H:%M:%S')}) = {time_diff:6.1f}秒")
                
                # 奇数番目と偶数番目のセット内時間差を計算
                if i % 2 == 1:  # 偶数番目（インデックス1, 3, 5...）
                    if i > 0:  # 前の奇数番目が存在する場合
                        prev_trim_time = trim_times[i-1][1]  # 前のtrim_image時刻
                        prev_csv_time = csv_times[i-1]       # 前のCSV時刻
                        
                        # セット内の時間差（奇数番目と偶数番目の差）
                        set_trim_diff = abs((trim_time - prev_trim_time).total_seconds())
                        
                        # CSVの行データが一致しているかチェック
                        csv_path = os.path.join(csv_base_dir, csv_files[0])
                        csv_row_match = False
                        try:
                            with open(csv_path, 'r', encoding='utf-8') as f:
                                reader = csv.reader(f)
                                next(reader)  # ヘッダー行をスキップ
                                rows = list(reader)
                                if i < len(rows) and i-1 < len(rows):
                                    # 奇数番目と偶数番目の行データを比較
                                    prev_row = rows[i-1]
                                    curr_row = rows[i]
                                    csv_row_match = prev_row == curr_row
                        except:
                            pass
                        
                        # 警告チェック
                        if set_trim_diff >= trim_interval_threshold:
                            warnings.append(f"    trim_image間隔警告: セット{(i // 2) + 1} 間隔 {set_trim_diff:.1f}秒 >= {trim_interval_threshold}秒")
                        
                        if csv_match_required and not csv_row_match:
                            warnings.append(f"    CSV行一致警告: セット{(i // 2) + 1} 行不一致")
                        
                        set_time_diffs.append({
                            'set_number': (i // 2) + 1,
                            'trim_diff': set_trim_diff,
                            'csv_match': csv_row_match,
                            'trim_file_prev': trim_times[i-1][0],
                            'trim_file_curr': trim_file
                        })
            
            # セット内時間差の統計を表示
            if set_time_diffs:
                print(f"\n  セット内時間差の詳細:")
                total_set_diff = 0
                max_set_diff = 0
                min_set_diff = float('inf')
                csv_match_count = 0
                
                for set_info in set_time_diffs:
                    match_status = "✓ 一致" if set_info['csv_match'] else "✗ 不一致"
                    print(f"    セット {set_info['set_number']:2d}: trim_image間隔 {set_info['trim_diff']:6.1f}秒, CSV行一致: {match_status}")
                    print(f"             前: {set_info['trim_file_prev']}")
                    print(f"             後: {set_info['trim_file_curr']}")
                    
                    total_set_diff += set_info['trim_diff']
                    max_set_diff = max(max_set_diff, set_info['trim_diff'])
                    min_set_diff = min(min_set_diff, set_info['trim_diff'])
                    if set_info['csv_match']:
                        csv_match_count += 1
                
                avg_set_diff = total_set_diff / len(set_time_diffs) if set_time_diffs else 0
                print(f"  セット内時間差統計:")
                print(f"    平均: {avg_set_diff:.1f}秒")
                print(f"    最大: {max_set_diff:.1f}秒")
                print(f"    最小: {min_set_diff:.1f}秒")
                print(f"    CSV行一致率: {csv_match_count}/{len(set_time_diffs)} ({csv_match_count/len(set_time_diffs)*100:.1f}%)")
            
            # 警告メッセージを表示
            if warnings:
                print(f"\n  ⚠️  警告メッセージ:")
                for warning in warnings:
                    print(warning)
            else:
                print(f"\n  ✓ 警告なし")
            
            avg_time_diff = total_time_diff / len(trim_times) if trim_times else 0
            print(f"\n  全体時刻差統計:")
            print(f"    平均: {avg_time_diff:.1f}秒")
            print(f"    最大: {max_time_diff:.1f}秒")
            print(f"    最小: {min_time_diff:.1f}秒")
            
            status = "✓ 時刻対応完了"
        else:
            print(f"  一対一対応: ✗ 不一致 (trim_image: {len(trim_times)}, CSV: {len(csv_times)})")
            status = "✗ 時刻対応失敗"
        
        total_trim_images += len(trim_times)
        total_csv_lines += len(csv_times)
        
        date_summary[date_dir] = {
            'trim_images': len(trim_times),
            'csv_lines': len(csv_times),
            'consistent': len(trim_times) == len(csv_times),
            'warnings': warnings
        }
        print()
    
    # 全体のサマリーを表示
    print("=" * 80)
    print("全体サマリー:")
    print("-" * 40)
    
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
    
    # 全体の警告サマリーを表示
    print("\n" + "=" * 80)
    print("全体警告サマリー:")
    print("-" * 40)
    
    # 各日付の警告を収集
    all_warnings = []
    for date_dir in sorted(date_summary.keys()):
        if 'warnings' in date_summary[date_dir]:
            all_warnings.extend([f"{date_dir}: {warning}" for warning in date_summary[date_dir]['warnings']])
    
    if all_warnings:
        print("⚠️  検出された警告:")
        for warning in all_warnings:
            print(f"  {warning}")
        print(f"\n総警告数: {len(all_warnings)} 件")
    else:
        print("✓ 警告なし - すべてのデータが正常です")

def main():
    """メイン関数"""
    print("trim_image と CSV 時刻対応・時刻差測定ツール")
    print("=" * 80)
    
    # 固定のディレクトリパス
    trim_base_directory = r"C:\Users\tyamaguchi\Desktop\smk_system\data\nir_image"
    csv_base_directory = r"C:\Users\tyamaguchi\Desktop\smk_system\data\nir_env\BP"
    
    # 警告閾値パラメータ（変更可能）
    time_diff_threshold = 300      # 時刻差の警告閾値（秒）
    trim_interval_threshold = 1    # trim_image間隔の警告閾値（秒）
    csv_match_required = True      # CSV行一致が必須かどうか
    
    print(f"trim_imageベースディレクトリ: {trim_base_directory}")
    print(f"CSVベースディレクトリ: {csv_base_directory}")
    print(f"警告閾値設定:")
    print(f"  時刻差閾値: {time_diff_threshold}秒")
    print(f"  trim_image間隔閾値: {trim_interval_threshold}秒")
    print(f"  CSV行一致必須: {'はい' if csv_match_required else 'いいえ'}")
    print()
    
    # 時刻対応・時刻差測定実行
    check_trim_image_csv_timing(trim_base_directory, csv_base_directory, 
                               time_diff_threshold, trim_interval_threshold, csv_match_required)

if __name__ == "__main__":
    main()
