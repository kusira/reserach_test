import cupy as cp
import numpy as np
import time

print("CuPy を使ったGPU計算の例")

# 1. CPU (NumPy) でデータを準備
# 大きな配列を作成して、GPUでの計算のメリットを示す
SIZE = 10000
cpu_array_a = np.random.rand(SIZE, SIZE).astype(np.float32)
cpu_array_b = np.random.rand(SIZE, SIZE).astype(np.float32)

print(f"NumPy 配列の形状: {cpu_array_a.shape}")
print("NumPy 配列 (A) の最初の数要素:\n", cpu_array_a[:2, :2])
print("NumPy 配列 (B) の最初の数要素:\n", cpu_array_b[:2, :2])

# 2. CuPy を使って GPU にデータを転送
print("\nデータをGPUに転送中...")
start_transfer = time.time()
gpu_array_a = cp.array(cpu_array_a)
gpu_array_b = cp.array(cpu_array_b)
end_transfer = time.time()
print(f"データ転送時間: {end_transfer - start_transfer:.4f} 秒")

# 3. GPU (CuPy) で計算を実行
print("GPUで計算を実行中 (行列乗算)...")
start_gpu_calc = time.time()
gpu_result = gpu_array_a @ gpu_array_b # 行列乗算
# または gpu_result = cp.matmul(gpu_array_a, gpu_array_b)
end_gpu_calc = time.time()
print(f"GPU計算時間: {end_gpu_calc - start_gpu_calc:.4f} 秒")

# 4. 結果を GPU から CPU に戻す (必要であれば)
print("\n結果をCPUに戻し中...")
start_get = time.time()
cpu_result = gpu_result.get() # .get() メソッドで GPU から CPU にデータを取得
end_get = time.time()
print(f"結果取得時間: {end_get - start_get:.4f} 秒")

print("\nGPU計算結果 (CPU上のNumPy配列として) の最初の数要素:\n", cpu_result[:2, :2])

# 参考: CPU (NumPy) で同じ計算を行った場合の時間比較
print("\n参考: CPU (NumPy) で同じ計算を実行中...")
start_cpu_calc = time.time()
cpu_true_result = cpu_array_a @ cpu_array_b
end_cpu_calc = time.time()
print(f"CPU計算時間: {end_cpu_calc - start_cpu_calc:.4f} 秒")

# 結果の検証 (オプション)
# GPUとCPUの結果が一致するか確認
# print("\n結果の最大絶対誤差:", np.max(np.abs(cpu_result - cpu_true_result)))