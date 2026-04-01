##Author：cheng hao
##Email: chenghao8425@163.com
##微信公众号：材料计算学习笔记
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress


# =========================
# 1) 拟合温度
# =========================
def process_temperature_data(
    input_file,
    output_temperature_file,
    output_mean_file,
    figure_file,
    num_blocks=20,
    num_chunks=50,
    position_factor=200,
):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    temperature_data = []
    chunk_positions = []
    current_block_temperatures = []

    for line in lines:
        parts = line.strip().split()

        if len(parts) == 3 and parts[0].isdigit():
            if current_block_temperatures:
                temperature_data.append(current_block_temperatures)
                current_block_temperatures = []
            continue

        if len(parts) == 4 and parts[0].isdigit():
            if len(chunk_positions) < num_chunks:
                chunk_positions.append(float(parts[1]) * position_factor)
            current_block_temperatures.append(float(parts[3]))

    if current_block_temperatures:
        temperature_data.append(current_block_temperatures)

    if not temperature_data:
        raise ValueError(f"未从温度文件中读取到有效数据: {input_file}")

    temperature_df = pd.DataFrame(temperature_data[:num_blocks]).T
    temperature_df.insert(0, "Position", chunk_positions)
    temperature_df["Position"] = temperature_df["Position"].round().astype(int)

    Path(output_temperature_file).parent.mkdir(parents=True, exist_ok=True)
    temperature_df.to_csv(output_temperature_file, sep='\t', index=False, header=False)

    mean_temperatures = temperature_df.iloc[:, 1:].replace(0, pd.NA).mean(axis=1)
    mean_df = pd.DataFrame({"Position": temperature_df["Position"], "Mean_Temperature": mean_temperatures})
    mean_df.to_csv(output_mean_file, sep='\t', index=False, header=False)

    plt.figure(figsize=(8, 6))
    plt.scatter(mean_df["Position"], mean_df["Mean_Temperature"], alpha=0.8, label='Temperature Data')
    plt.xlabel('Position (x)')
    plt.ylabel('Mean Temperature (K)')
    plt.title('Mean Temperature vs Position')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_file, dpi=300)
    plt.close()

    return mean_df


# ===================================
# 2) 热流线性拟合
# ===================================
def fit_heat_power_w(heat_flux_file, figure_file, time_ps_factor=0.001):
    data = np.loadtxt(heat_flux_file, comments='#')
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.shape[1] < 3:
        raise ValueError(f"热流文件列数不足，至少需要3列: {heat_flux_file}")

    time_ps = data[:, 0] * time_ps_factor
    f_hot = data[:, 1]
    f_cold = data[:, 2]

    slope_hot, intercept_hot, _, _, _ = linregress(time_ps, f_hot)
    slope_cold, intercept_cold, _, _, _ = linregress(time_ps, f_cold)

    slope_hot_w = slope_hot * 1.60218e-19 / 1.0e-12
    slope_cold_w = slope_cold * 1.60218e-19 / 1.0e-12
    P_avg = (abs(slope_hot_w) + abs(slope_cold_w)) / 2.0

    plt.figure(figsize=(10, 6))
    plt.plot(time_ps, f_hot, 'r.', alpha=0.6, label='Hot data')
    plt.plot(time_ps, f_cold, 'b.', alpha=0.6, label='Cold data')
    plt.plot(time_ps, slope_hot * time_ps + intercept_hot, 'r-', label=f'Hot fit: {slope_hot:.4f} eV/ps')
    plt.plot(time_ps, slope_cold * time_ps + intercept_cold, 'b-', label=f'Cold fit: {slope_cold:.4f} eV/ps')
    plt.xlabel('Time (ps)')
    plt.ylabel('Energy Exchange (eV)')
    plt.title('Energy Exchange Linear Fit')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_file, dpi=300)
    plt.close()

    return P_avg, time_ps, f_hot, f_cold, slope_hot, slope_cold, (intercept_hot, intercept_cold)


# ===================================
# 3) 单区间温度线性拟合 & 热导率计算
# ===================================
def fit_temperature_gradient_and_k(mean_temp_file, fit_range, contact_area, P_avg, figure_file):
    data = []
    with open(mean_temp_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                data.append([float(parts[0]), float(parts[1])])

    data = np.array(data)
    if len(data) < 2:
        raise ValueError(f"平均温度文件数据不足: {mean_temp_file}")

    x = data[:, 0]
    T = data[:, 1]

    x0, x1 = fit_range
    mask = (x >= x0) & (x <= x1)
    x_fit = x[mask]
    T_fit = T[mask]
    if len(x_fit) < 2:
        raise ValueError(f"温度拟合区间内数据点不足: fit_range={fit_range}")

    slope_T, intercept_T, _, _, _ = linregress(x_fit, T_fit)

    plt.figure(figsize=(8, 6))
    plt.scatter(x, T, alpha=0.75, label='Mean Temp')
    plt.plot(x_fit, slope_T * x_fit + intercept_T, 'r--', label=f'Fit [{x0}, {x1}] slope={slope_T:.4f} K/xunit')
    plt.xlabel('Position (x)')
    plt.ylabel('Mean Temperature (K)')
    plt.title('Temperature Linear Fit (single range)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_file, dpi=300)
    plt.close()

    q = P_avg / contact_area
    gradT = slope_T * 1e10
    k = q / abs(gradT)

    return k, gradT, slope_T, intercept_T, q


# =========================
# 配置文件解析
# =========================
def parse_scalar(text: str):
    s = text.strip()
    low = s.lower()
    if low in {'true', 'yes', 'on'}:
        return True
    if low in {'false', 'no', 'off'}:
        return False
    if low in {'none', 'null'}:
        return None

    try:
        if s.startswith('0') and len(s) > 1 and s[1].isdigit() and not s.startswith('0.'):
            raise ValueError
        return int(s)
    except ValueError:
        pass

    try:
        return float(s)
    except ValueError:
        return s


def parse_value(text: str):
    s = text.strip()
    if ',' in s:
        return [parse_scalar(part) for part in s.split(',') if part.strip()]
    return parse_scalar(s)


def load_rc_config(config_path: str) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        'defaults': {},
        'case_overrides': {},
    }
    current_section = 'global'
    current_case = None

    with open(config_path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue

            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1].strip()
                current_case = None
                if section.lower() == 'defaults':
                    current_section = 'defaults'
                elif section.lower().startswith('case:'):
                    current_section = 'case'
                    current_case = section.split(':', 1)[1].strip()
                    cfg['case_overrides'].setdefault(current_case, {})
                else:
                    current_section = 'global'
                continue

            if '=' not in line:
                raise ValueError(f"配置文件格式错误，缺少 '=' : {raw_line.strip()}")

            key, value = line.split('=', 1)
            key = key.strip()
            value = parse_value(value)

            if current_section == 'global':
                cfg[key] = value
            elif current_section == 'defaults':
                cfg['defaults'][key] = value
            elif current_section == 'case':
                cfg['case_overrides'][current_case][key] = value

    cfg.setdefault('scan_mode', 'list')
    cfg.setdefault('case_dirs', [])
    cfg.setdefault('batch_summary_name', 'batch_results_summary.csv')

    defaults = cfg['defaults']
    defaults.setdefault('temp_input_name', 'temp.CNT.txt')
    defaults.setdefault('heat_flux_input_name', 'heat_flux_exchange.txt')
    defaults.setdefault('extracted_temp_name', 'extracted_temperature_data.txt')
    defaults.setdefault('mean_temp_name', 'mean_temperature_data.txt')
    defaults.setdefault('mean_temp_figure_name', 'mean_temperature_vs_position_no_zero.png')
    defaults.setdefault('heat_flux_figure_name', 'energy_flux_fit.png')
    defaults.setdefault('temp_fit_figure_name', 'temperature_fit_single_range.png')
    defaults.setdefault('summary_name', 'result_summary.csv')
    defaults.setdefault('time_ps_factor', 0.001)

    required_top = ['root_dir']
    required_defaults = ['num_blocks', 'num_chunks', 'position_factor', 'contact_area', 'fit_range']

    for key in required_top:
        if key not in cfg:
            raise ValueError(f"配置文件缺少顶层参数: {key}")
    for key in required_defaults:
        if key not in defaults:
            raise ValueError(f"配置文件 [defaults] 缺少参数: {key}")

    if not isinstance(defaults['fit_range'], list) or len(defaults['fit_range']) != 2:
        raise ValueError("fit_range 必须写成两个值，例如: fit_range = 34, 160")

    return cfg


def merge_case_config(defaults: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = defaults.copy()
    merged.update(override or {})
    return merged


def discover_case_dirs(root_dir: Path, mode: str, listed_cases: List[str]) -> List[Path]:
    if mode == 'list':
        return [root_dir / str(name) for name in listed_cases]
    if mode == 'auto':
        return sorted([p for p in root_dir.iterdir() if p.is_dir()])
    raise ValueError("scan_mode 只能是 'list' 或 'auto'")


def process_one_case(case_dir: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    temp_input = case_dir / cfg['temp_input_name']
    heat_flux_input = case_dir / cfg['heat_flux_input_name']

    extracted_temp_file = case_dir / cfg['extracted_temp_name']
    mean_temp_file = case_dir / cfg['mean_temp_name']
    mean_temp_fig = case_dir / cfg['mean_temp_figure_name']
    heat_flux_fig = case_dir / cfg['heat_flux_figure_name']
    temp_fit_fig = case_dir / cfg['temp_fit_figure_name']
    summary_file = case_dir / cfg['summary_name']

    if not temp_input.exists():
        raise FileNotFoundError(f"缺少温度文件: {temp_input}")
    if not heat_flux_input.exists():
        raise FileNotFoundError(f"缺少热流文件: {heat_flux_input}")

    process_temperature_data(
        input_file=temp_input,
        output_temperature_file=extracted_temp_file,
        output_mean_file=mean_temp_file,
        figure_file=mean_temp_fig,
        num_blocks=cfg['num_blocks'],
        num_chunks=cfg['num_chunks'],
        position_factor=cfg['position_factor'],
    )

    P_avg, _, _, _, slope_hot, slope_cold, (intercept_hot, intercept_cold) = fit_heat_power_w(
        heat_flux_input,
        figure_file=heat_flux_fig,
        time_ps_factor=cfg['time_ps_factor'],
    )

    k, gradT, slope_T, intercept_T, q = fit_temperature_gradient_and_k(
        mean_temp_file=mean_temp_file,
        fit_range=tuple(cfg['fit_range']),
        contact_area=cfg['contact_area'],
        P_avg=P_avg,
        figure_file=temp_fit_fig,
    )

    result = {
        'case': case_dir.name,
        'status': 'ok',
        'P_avg_W': P_avg,
        'heat_flux_W_m2': q,
        'gradT_K_m': gradT,
        'k_W_mK': k,
        'slope_hot_eV_ps': slope_hot,
        'slope_cold_eV_ps': slope_cold,
        'intercept_hot': intercept_hot,
        'intercept_cold': intercept_cold,
        'temp_slope_K_per_A': slope_T,
        'temp_intercept': intercept_T,
        'fit_range_start': cfg['fit_range'][0],
        'fit_range_end': cfg['fit_range'][1],
        'contact_area_m2': cfg['contact_area'],
        'position_factor': cfg['position_factor'],
        'time_ps_factor': cfg['time_ps_factor'],
        'num_blocks': cfg['num_blocks'],
        'num_chunks': cfg['num_chunks'],
    }

    pd.DataFrame([result]).to_csv(summary_file, index=False)
    return result


def main(config_path='rc.in'):
    cfg = load_rc_config(config_path)
    root_dir = Path(str(cfg['root_dir'])).resolve()
    root_dir.mkdir(parents=True, exist_ok=True)

    defaults = cfg['defaults']
    scan_mode = str(cfg.get('scan_mode', 'list'))
    listed_cases = cfg.get('case_dirs', [])
    if isinstance(listed_cases, str):
        listed_cases = [listed_cases]
    case_overrides = cfg.get('case_overrides', {})
    summary_csv_name = str(cfg.get('batch_summary_name', 'batch_results_summary.csv'))

    case_dirs = discover_case_dirs(root_dir, scan_mode, listed_cases)
    if not case_dirs:
        raise ValueError(f"在 {root_dir} 下没有找到待处理文件夹。")

    all_results = []
    for case_dir in case_dirs:
        case_cfg = merge_case_config(defaults, case_overrides.get(case_dir.name, {}))
        try:
            print(f"\n>>> 开始处理: {case_dir.name}")
            result = process_one_case(case_dir, case_cfg)
            print(f"    完成: k = {result['k_W_mK']:.6e} W/m·K")
        except Exception as e:
            result = {
                'case': case_dir.name,
                'status': 'failed',
                'error': str(e),
            }
            print(f"    失败: {e}")
        all_results.append(result)

    summary_csv = root_dir / summary_csv_name
    pd.DataFrame(all_results).to_csv(summary_csv, index=False)
    print(f"\n>>> 全部处理完成，汇总结果已保存到: {summary_csv}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
