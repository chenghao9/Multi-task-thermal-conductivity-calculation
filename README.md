# Multi-task-thermal-conductivity-calculation
Rapidly process NEMD simulation data to calculate thermal conductivity (LAMMPS software)
# ==============================
##Author：cheng hao
##Email: chenghao8425@163.com
##微信公众号：材料计算学习笔记
# ==============================

1. 脚本用途

TC_rc.py 用于**批量处理多个分子动力学算例文件夹中的温度文件和热流文件**，并自动计算每个算例的热导率 `k`。

脚本适用于如下场景：
有多个子文件夹（如 `0`、`10`、`20`、`30` 等）
每个子文件夹中都包含一个温度分布文件和一个热流交换文件
依次处理这些文件夹
将结果分别保存到各自文件夹中，并在根目录下生成一个总汇总表
通过一个简单的文本输入文件（如 `rc\\\_k.in`）统一控制参数

2. 主要功能

本脚本完成以下工作：

1. 读取每个文件夹中的温度文件
2. 提取温度数据，计算平均温度分布
3. 对热流交换文件进行线性拟合，得到平均热功率
4. 对温度分布在指定区间内做线性拟合，得到温度梯度
5. 根据热流密度与温度梯度计算热导率
6. 将每个文件夹的结果分别保存到对应文件夹
7. 在根目录下输出一个批处理汇总表 `results\\\_summary.csv`

3. 依赖环境

建议使用 Python 3.9 及以上版本。
需要安装以下 Python 包：

pip install numpy pandas matplotlib scipy

4. 计算流程

对每个文件夹，脚本按以下流程计算：
### 第一步：处理温度数据

读取前 num_blocks个 block
每个 block 中读取 num_chunks个位置点
将位置乘以 position_factor
输出： extracted_temperature_data.txt，mean_temperature_data.txt，mean_temperature_vs_position_no_zero.png`

### 第二步：拟合热流文件

对热端和冷端能量交换分别做线性拟合
输出：energy_flux_fit.png

### 第三步：拟合温度梯度并计算热导率

在 `fit\\\_range` 指定区间内对平均温度做线性拟合得到温度梯度和热流密度，计算热导率
输出：temperature_fit_single_range.png和result_summary.csv

5. rc_k.in文件参数说明
### 顶层参数
`root\\\_dir`：所有 case 子文件夹所在根目录
可以写绝对路径
也可以写 `.`，表示当前目录

`scan\\\_mode`：扫描模式
`list`：只处理 `case\\\_dirs` 中列出的文件夹
`auto`：自动处理 `root\\\_dir` 下所有子文件夹

`case\\\_dirs`：需要处理的 case 文件夹名列表
示例：`case\\\_dirs = 0, 10, 20`
若只处理一个文件夹，也可写：`case\\\_dirs = 0,`

`batch\\\_summary\\\_name`：批处理汇总结果文件名

### `\\\[defaults]` 中的参数

#### 输入输出文件名

`temp\\\_input\\\_name`：温度输入文件名
`heat\\\_flux\\\_input\\\_name`：热流输入文件名
`extracted\\\_temp\\\_name`：提取后的温度明细文件名
`mean\\\_temp\\\_name`：平均温度分布文件名
`mean\\\_temp\\\_figure\\\_name`：平均温度分布图文件名
`heat\\\_flux\\\_figure\\\_name`：热流拟合图文件名
`temp\\\_fit\\\_figure\\\_name`：温度拟合图文件名
`summary\\\_name`：单个 case 结果汇总文件名

#### 温度处理参数

`num\\\_blocks`：用于平均的 block 数
`num\\\_chunks`：每个 block 中读取的空间分块数
`position\\\_factor`：位置缩放因子

#### 热流处理参数

`time\\\_ps\\\_factor`：热流文件第一列换算为 ps 的系数

#### 热导率计算参数

`contact\\\_area`：接触面积，单位 `m^2`
`fit\\\_range`：拟合温度梯度的区间，如 `34, 160`

### `\\\[case:xxx]` 覆盖参数

如果某个 case 的参数与默认值不同，可以写单独覆盖段。例如：

```

\\\[case:10]

fit\\\_range = 40, 150

time\\\_ps\\\_factor = 0.001

contact\\\_area = 2.2e-18

```
表示：只有文件夹 `10` 使用这组参数，其他文件夹仍使用 `\\\[defaults]` 中的参数。
---

## 6. 运行方法

进入脚本所在目录后，在命令行运行：

```bash

python TC\\\_rc.py rc\\\_k.in

```
---

## 7. 输出文件说明

### 每个 case 文件夹下会生成

`extracted\\\_temperature\\\_data.txt`：提取后的温度明细数据
`mean\\\_temperature\\\_data.txt`：平均温度分布数据
`mean\\\_temperature\\\_vs\\\_position\\\_no\\\_zero.png`：平均温度分布图
`energy\\\_flux\\\_fit.png`：热流拟合图
`temperature\\\_fit\\\_single\\\_range.png`：温度拟合图
`result\\\_summary.csv`：单个 case 结果汇总表

### 根目录下会生成
`batch\\\_results\\\_summary.csv`：所有 case 的汇总结果表
---

## 8. result_summary.csv 各列含义

`case`：算例名称（文件夹名）
`status`：处理状态，`ok` 表示成功，`failed` 表示失败
`P\\\_avg\\\_W`：平均热功率，单位 W
`heat\\\_flux\\\_W\\\_m2`：热流密度，单位 W/m²
`gradT\\\_K\\\_m`：温度梯度，单位 K/m
`k\\\_W\\\_mK`：热导率，单位 W/(m·K)
`slope\\\_hot\\\_eV\\\_ps`：热端能量交换拟合斜率，单位 eV/ps
`slope\\\_cold\\\_eV\\\_ps`：冷端能量交换拟合斜率，单位 eV/ps
`intercept\\\_hot`：热端拟合截距
`intercept\\\_cold`：冷端拟合截距
`temp\\\_slope\\\_K\\\_per\\\_A`：温度拟合原始斜率，单位 K/Å
`temp\\\_intercept`：温度拟合截距
`fit\\\_range\\\_start`：温度拟合区间起点
`fit\\\_range\\\_end`：温度拟合区间终点
`contact\\\_area\\\_m2`：接触面积，单位 m²
`position\\\_factor`：位置缩放因子
`time\\\_ps\\\_factor`：时间步换算为 ps 的系数
`num\\\_blocks`：参与平均的 block 数
`num\\\_chunks`：每个 block 中读取的 chunk 数

---
## 9. 文件对应关系

- 主程序：`TC1\\\_batch\\\_rc\\\_v3.py`
- 参数文件模板：`rc\\\_k.in`
- 单 case 结果：各子文件夹下 `result\\\_summary.csv`
- 批处理汇总：根目录下 `batch\\\_results\\\_summary.csv`

---
