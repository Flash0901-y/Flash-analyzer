"""
FLASH 闪光音频分析器 - Streamlit Web 版
v5.0 — 完全重构：仪表盘布局/SVG 闪电/科技风格/网格系统
"""
import streamlit as st
import sys, os, tempfile, time
import warnings
import numpy as np

# ==================== 配置 ====================
MAX_FILE_SIZE_MB = 50
BPM_MIN = 60
BPM_MAX = 200
BANDS_DEF = [
    ('sub_bass', 20, 60, 'Sub Bass', '重低音'),
    ('bass', 60, 250, 'Bass', '低音'),
    ('low_mid', 250, 500, 'Low Mid', '低中频'),
    ('mid', 500, 2000, 'Mid', '中频'),
    ('high_mid', 2000, 4000, 'High Mid', '高中频'),
    ('presence', 4000, 6000, 'Presence', '临场感'),
    ('high', 6000, 20000, 'High', '高频'),
]
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# ==================== 全新 CSS 设计 ====================
CUSTOM_CSS = """
<style>
/* ===== 导入字体 ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

/* ===== 全局重置 ===== */
* {
    box-sizing: border-box;
}

.stApp {
    background: #030308;
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
}

/* ===== 隐藏 Streamlit 默认元素 ===== */
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden !important;
    display: none !important;
}

/* ===== 网格背景动画 ===== */
.grid-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

.grid-background::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(ellipse at 50% 0%, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

/* ===== 主容器 ===== */
.main-container {
    position: relative;
    z-index: 1;
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* ===== 头部区域 ===== */
.header-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 30px 0;
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    margin-bottom: 40px;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 20px;
}

.flash-logo {
    width: 80px;
    height: 80px;
    filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.6));
    animation: glow 2s ease-in-out infinite;
}

@keyframes glow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.6)); }
    50% { filter: drop-shadow(0 0 40px rgba(251, 191, 36, 0.9)); }
}

.title-section h1 {
    font-size: 42px;
    font-weight: 900;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -1px;
}

.title-section p {
    color: #6b7280;
    font-size: 16px;
    margin: 8px 0 0 0;
    font-family: 'JetBrains Mono', monospace;
}

/* ===== 指标卡片网格 ===== */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 40px;
}

.metric-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(31, 41, 55, 0.8));
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    transform: scaleX(0);
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 60px rgba(59, 130, 246, 0.1);
}

.metric-card:hover::before {
    transform: scaleX(1);
}

.metric-icon {
    font-size: 28px;
    margin-bottom: 12px;
}

.metric-label {
    color: #9ca3af;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 32px;
    font-weight: 700;
    color: #f3f4f6;
    font-family: 'JetBrains Mono', monospace;
}

.metric-unit {
    font-size: 14px;
    color: #6b7280;
    margin-left: 4px;
}

/* ===== 内容区域 ===== */
.content-section {
    background: rgba(17, 24, 39, 0.5);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
}

.section-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.section-title {
    font-size: 24px;
    font-weight: 700;
    color: #f3f4f6;
    margin: 0;
}

/* ===== 频率条 ===== */
.frequency-item {
    margin-bottom: 16px;
}

.frequency-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.frequency-name {
    color: #d1d5db;
    font-size: 14px;
    font-weight: 500;
}

.frequency-name-cn {
    color: #6b7280;
    font-size: 12px;
    margin-left: 8px;
}

.frequency-percent {
    color: #fbbf24;
    font-size: 14px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}

.frequency-track {
    height: 12px;
    background: rgba(31, 41, 55, 0.8);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
}

.frequency-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
    border-radius: 6px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
}

.frequency-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* ===== 文件上传 ===== */
.uploader-container {
    background: rgba(17, 24, 39, 0.8);
    border: 2px dashed rgba(59, 130, 246, 0.3);
    border-radius: 20px;
    padding: 60px 40px;
    text-align: center;
    transition: all 0.3s ease;
    margin-bottom: 30px;
}

.uploader-container:hover {
    border-color: rgba(59, 130, 246, 0.6);
    background: rgba(17, 24, 39, 0.9);
}

/* ===== 按钮 ===== */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
    font-family: 'Inter', sans-serif;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(59, 130, 246, 0.6);
}

/* ===== EQ 卡片 ===== */
.eq-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(31, 41, 55, 0.9));
    border-left: 4px solid #fbbf24;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
}

.eq-card:hover {
    transform: translateX(8px);
    box-shadow: 0 8px 30px rgba(251, 191, 36, 0.2);
}

.eq-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}

.eq-icon {
    font-size: 20px;
}

.eq-title {
    color: #fbbf24;
    font-weight: 700;
    font-size: 16px;
    font-family: 'JetBrains Mono', monospace;
}

.eq-reason {
    color: #9ca3af;
    font-size: 14px;
    line-height: 1.5;
}

/* ===== 下载按钮特殊样式 ===== */
.download-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4) !important;
}

.download-btn:hover {
    box-shadow: 0 8px 30px rgba(16, 185, 129, 0.6) !important;
}

/* ===== 模式切换 ===== */
.mode-selector {
    background: rgba(17, 24, 39, 0.8);
    border-radius: 12px;
    padding: 6px;
    display: inline-flex;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
    .header-section {
        flex-direction: column;
        text-align: center;
        gap: 20px;
    }
    
    .title-section h1 {
        font-size: 32px;
    }
    
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .metric-value {
        font-size: 24px;
    }
}
</style>

<!-- 网格背景 -->
<div class="grid-background"></div>
"""

# ==================== SVG 闪电图标 ====================
FLASH_SVG = """
<svg class="flash-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="flashGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#fbbf24;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#f59e0b;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#d97706;stop-opacity:1" />
        </linearGradient>
        <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    <polygon points="50,5 20,55 45,55 35,95 80,40 55,40" 
             fill="url(#flashGrad)" 
             filter="url(#glow)"
             stroke="#fbbf24"
             stroke-width="2"/>
</svg>
"""

# ==================== 工具函数 ====================
def format_duration(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def correct_bpm(bpm_val):
    try:
        bpm = float(bpm_val)
        if not np.isfinite(bpm) or bpm <= 0:
            return 0.0
        while bpm < BPM_MIN and bpm > 0:
            bpm *= 2
        while bpm > BPM_MAX:
            bpm /= 2
        return round(bpm, 1)
    except:
        return 0.0

def true_peak_detection(y, sr):
    from scipy.interpolate import interp1d
    n = len(y)
    x_orig = np.arange(n)
    x_upsampled = np.linspace(0, n - 1, n * 4)
    f = interp1d(x_orig, y, kind='cubic', bounds_error=False, fill_value=0)
    y_upsampled = f(x_upsampled)
    true_peak = float(np.max(np.abs(y_upsampled)))
    true_peak_db = round(20 * np.log10(true_peak + 1e-10), 2)
    return true_peak, true_peak_db

def generate_report(res, filename):
    lines = []
    lines.append("=" * 60)
    lines.append("       FLASH 闪光音频分析报告")
    lines.append("=" * 60)
    lines.append(f"文件名：{filename}")
    lines.append(f"分析时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("【核心参数】")
    lines.append(f"  BPM:          {res.get('bpm', 0)}")
    lines.append(f"  调性：{res.get('key', '未知')} ({res.get('key_confidence', 0):.0%})")
    lines.append(f"  动态范围：{res.get('crest_factor_db', 0)} dB")
    lines.append(f"  采样率：{res.get('sample_rate', 0)/1000:.1f} kHz")
    lines.append(f"  时长：{format_duration(res.get('duration_sec', 0))}")
    lufs_est = " (估计值)" if res.get('lufs_estimated') else ""
    lines.append(f"  LUFS:         {res.get('lufs_integrated', 0)} dB{lufs_est}")
    lines.append(f"  声道数：{res.get('channels', 1)}")
    lines.append(f"  True Peak:    {res.get('true_peak_db', 0)} dBFS")
    lines.append("")
    lines.append("【频率分布】")
    for k, v in res['frequency'].items():
        lines.append(f"  {v['label']:<18} {v['pct']:>5}%")
    lines.append("")
    if 'stereo' in res and res['stereo']:
        lines.append("【立体声场】")
        st_info = res['stereo']
        lines.append(f"  声道相关性：{st_info['correlation']:.3f}")
        lines.append(f"  左声道 RMS:    {st_info['left_rms']}")
        lines.append(f"  右声道 RMS:    {st_info['right_rms']}")
        lines.append("")
    if 'eq_suggestions' in res and res['eq_suggestions']:
        lines.append("【EQ 参数推荐】")
        for i, eq in enumerate(res['eq_suggestions'], 1):
            lines.append(f"  {i}. {eq['desc']} → {eq['reason']}")
        lines.append("")
    if 'mastering' in res:
        m = res['mastering']
        lines.append("【母带参数】")
        lines.append(f"  目标 LUFS: {m['target_lufs']} dB")
        lines.append(f"  需要增益：{m['gain_needed']:+} dB")
        lines.append("")
    lines.append("=" * 60)
    lines.append("         FLASH Audio Analyzer v5.0")
    lines.append("=" * 60)
    return "\n".join(lines)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title='FLASH 音频分析器',
    page_icon='⚡',
    layout='wide',
    initial_sidebar_state='collapsed'
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==================== 依赖检查 ====================
@st.cache_resource
def check_dependencies():
    engine = 'minimal'
    missing = []
    features = {}
    try:
        import librosa
        engine = 'librosa'
        features['librosa'] = True
    except ImportError:
        missing.append('librosa')
        features['librosa'] = False
    try:
        import pyloudnorm
        features['pyloudnorm'] = True
    except ImportError:
        missing.append('pyloudnorm')
        features['pyloudnorm'] = False
    try:
        from scipy.interpolate import interp1d
        features['scipy'] = True
    except ImportError:
        missing.append('scipy')
        features['scipy'] = False
    return engine, missing, features

ENGINE, MISSING_PKGS, FEATURES = check_dependencies()

# ==================== 核心分析函数 ====================
def load_audio_librosa(filepath):
    import librosa
    y, sr = librosa.load(filepath, sr=None, mono=False)
    ym = librosa.to_mono(y) if y.ndim > 1 else y
    dur = librosa.get_duration(y=ym, sr=sr)
    return y, ym, sr, dur

def detect_bpm_librosa(y, sr):
    import librosa
    ta = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(ta, tuple):
        ta = ta[0]
    if hasattr(ta, '__getitem__') and not isinstance(ta, (float, int, str)):
        ta = ta[0]
    return correct_bpm(ta)

def detect_key_librosa(y, sr):
    import librosa
    def _kk_vote(cf):
        rv = {n: 0.0 for n in NOTE_NAMES}
        mm = {n: {"大": 0.0, "小": 0.0} for n in NOTE_NAMES}
        for fi in range(cf.shape[1]):
            cv = cf[:, fi]
            for s in range(12):
                sh = np.roll(cv, s)
                if np.std(sh) < 1e-8:
                    continue
                cmaj = float(np.corrcoef(sh, MAJOR_PROFILE)[0, 1])
                cmin = float(np.corrcoef(sh, MINOR_PROFILE)[0, 1])
                r = (12 - s) % 12
                if cmaj > 0 or cmin > 0:
                    rv[NOTE_NAMES[r]] += max(cmaj, 0) + max(cmin, 0)
                if cmaj > 0:
                    mm[NOTE_NAMES[r]]["大"] += cmaj
                if cmin > 0:
                    mm[NOTE_NAMES[r]]["小"] += cmin
        return rv, mm
    def _scale_vote(cf):
        rv = {n: 0.0 for n in NOTE_NAMES}
        for fi in range(cf.shape[1]):
            cv = cf[:, fi]
            for r in range(12):
                major_scale = [(r + i) % 12 for i in [0, 2, 4, 5, 7, 9, 11]]
                minor_scale = [(r + i) % 12 for i in [0, 2, 3, 5, 7, 8, 10]]
                major_in = float(np.mean([cv[i] for i in major_scale]))
                minor_in = float(np.mean([cv[i] for i in minor_scale]))
                rv[NOTE_NAMES[r]] += max(0, major_in) + max(0, minor_in)
        return rv
    cf = librosa.feature.chroma_stft(y=y, sr=sr)
    cm = np.mean(cf, axis=1)
    rv_kk, mm_kk = _kk_vote(cf)
    bk_kk = max(rv_kk, key=rv_kk.get)
    ri_kk = NOTE_NAMES.index(bk_kk)
    kk_major = mm_kk[bk_kk]["大"] >= mm_kk[bk_kk]["小"]
    kk_key = bk_kk + ('大调' if kk_major else '小调')
    rv_sm = _scale_vote(cf)
    bk_sm = max(rv_sm, key=rv_sm.get)
    ri_sm = NOTE_NAMES.index(bk_sm)
    M3 = cm[(ri_sm + 4) % 12]
    m3 = cm[(ri_sm + 3) % 12]
    sm_key = bk_sm + ('大调' if M3 > m3 else '小调')
    if ri_kk == (ri_sm + 7) % 12 and cm[ri_kk] / (cm[ri_sm] + 1e-10) > 1.2:
        best_key = sm_key
    else:
        best_key = kk_key
    total = mm_kk[bk_kk]["大"] + mm_kk[bk_kk]["小"]
    confidence = abs(mm_kk[bk_kk]["大"] - mm_kk[bk_kk]["小"]) / (total + 1e-10) if total > 0 else 0
    return best_key, round(min(confidence, 1.0), 3)

def analyze_spectrum(y, sr):
    import librosa
    D = librosa.stft(y, n_fft=4096)
    mag = np.abs(D).astype(np.float64)
    fr = librosa.fft_frequencies(sr=sr, n_fft=4096)
    total_energy = float(np.sum(mag ** 2))
    freq_bands = {}
    for k, lo, hi, la_en, la_cn in BANDS_DEF:
        msk = (fr >= lo) & (fr < hi)
        energy = float(np.sum(mag[msk] ** 2))
        pct = round(energy / total_energy * 100, 1) if total_energy > 0 else 0
        freq_bands[k] = {'label': la_en, 'label_cn': la_cn, 'pct': pct}
    return freq_bands, mag, fr

def analyze_dynamics(y, sr):
    import librosa
    peak = float(np.max(np.abs(y)))
    overall_rms = float(np.sqrt(np.mean(y ** 2)))
    crest_db = round(20 * np.log10(peak / overall_rms), 1) if overall_rms > 0 else 0
    avg_rms = float(np.mean(librosa.feature.rms(y=y)[0]))
    sc = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))
    lufs = 0
    lufs_estimated = False
    if FEATURES.get('pyloudnorm'):
        try:
            import pyloudnorm
            meter = pyloudnorm.Meter(sr)
            lufs = meter.integrated_loudness(y)
        except Exception:
            pass
    if lufs == 0:
        rms_val = float(np.sqrt(np.mean(y ** 2)))
        lufs = round(20 * np.log10(rms_val + 1e-10) - 0.691, 1)
        lufs_estimated = True
    true_peak_val, true_peak_db = true_peak_detection(y, sr)
    return {
        'rms': round(avg_rms, 4),
        'peak': round(peak, 4),
        'crest_factor_db': crest_db,
        'spectral_centroid': int(sc),
        'lufs_integrated': round(lufs, 1),
        'lufs_estimated': lufs_estimated,
        'true_peak': round(true_peak_val, 4),
        'true_peak_db': true_peak_db,
    }

def analyze_stereo_pro(y_stereo, sr):
    if y_stereo.ndim <= 1 or y_stereo.shape[0] < 2:
        return None
    import librosa
    left = y_stereo[0]
    right = y_stereo[1]
    corr = float(np.corrcoef(left, right)[0, 1])
    left_rms = round(float(np.sqrt(np.mean(left ** 2))), 4)
    right_rms = round(float(np.sqrt(np.mean(right ** 2))), 4)
    return {
        'correlation': corr,
        'left_rms': left_rms,
        'right_rms': right_rms,
    }

def generate_eq_suggestions(freq_bands):
    suggestions = []
    su = freq_bands.get('sub_bass', {}).get('pct', 0)
    ba = freq_bands.get('bass', {}).get('pct', 0)
    lm = freq_bands.get('low_mid', {}).get('pct', 0)
    hm = freq_bands.get('high_mid', {}).get('pct', 0)
    hv = freq_bands.get('high', {}).get('pct', 0)
    if lm > 25:
        suggestions.append({'type': 'cut', 'desc': '300Hz Q1.4 -2dB', 'reason': f'低中频浑浊 ({lm}%)'})
    if hm > 20:
        suggestions.append({'type': 'cut', 'desc': '3.5kHz Q2.0 -1.5dB', 'reason': f'齿音过重 ({hm}%)'})
    if hv < 8:
        suggestions.append({'type': 'boost', 'desc': '12kHz +1.5dB', 'reason': '高频空气感不足'})
    if ba > 35:
        suggestions.append({'type': 'cut', 'desc': '120Hz Q1.0 -2dB', 'reason': f'低音过多 ({ba}%)'})
    return suggestions

def generate_mastering_suggestions(lufs, crest, sc):
    target_lufs = -14 if lufs < -16 else (-10 if lufs < -10 else lufs)
    if crest > 14:
        compressor = {'threshold': -20, 'ratio': 1.5, 'attack': 30, 'release': 200, 'note': '动态大，温和压缩'}
    elif crest > 8:
        compressor = {'threshold': -18, 'ratio': 2.0, 'attack': 20, 'release': 150, 'note': '标准流行设置'}
    else:
        compressor = {'threshold': -15, 'ratio': 2.5, 'attack': 15, 'release': 100, 'note': '动态小，谨慎压缩'}
    return {
        'target_lufs': target_lufs,
        'gain_needed': round(target_lufs - lufs, 1),
        'compressor': compressor,
        'limiter': {'threshold': -0.3, 'ceiling': -0.1},
    }

@st.cache_data(show_spinner=False, ttl=3600)
def analyze_audio_cached(file_content, filename):
    return analyze_audio(file_content, filename)

def analyze_audio(file_content, filename):
    ext = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
        tmp.write(file_content)
        tmp.flush()
        if ENGINE == 'librosa':
            y_stereo, y_mono, sr, dur = load_audio_librosa(tmp.name)
            channels = y_stereo.shape[0] if y_stereo.ndim > 1 else 1
            result = {
                'sample_rate': sr,
                'duration_sec': round(dur, 2),
                'channels': channels,
                'filename': filename,
            }
            result['bpm'] = detect_bpm_librosa(y_mono, sr)
            result['key'], result['key_confidence'] = detect_key_librosa(y_mono, sr)
            result['frequency'], mag, fr = analyze_spectrum(y_mono, sr)
            dyn = analyze_dynamics(y_mono, sr)
            result.update(dyn)
            stereo_info = analyze_stereo_pro(y_stereo, sr)
            if stereo_info:
                result['stereo'] = stereo_info
            result['eq_suggestions'] = generate_eq_suggestions(result['frequency'])
            result['mastering'] = generate_mastering_suggestions(
                result['lufs_integrated'],
                result['crest_factor_db'],
                result['spectral_centroid']
            )
            return result
        else:
            return None

def generate_suggestions(res):
    fq = res['frequency']
    sg = []
    su = fq.get('sub_bass', {}).get('pct', 0)
    ba = fq.get('bass', {}).get('pct', 0)
    lm = fq.get('low_mid', {}).get('pct', 0)
    hm = fq.get('high_mid', {}).get('pct', 0)
    hv = fq.get('high', {}).get('pct', 0)
    cf = res.get('crest_factor_db', 0)
    lufs = res.get('lufs_integrated', 0)
    if su > 35: sg.append(f'🔴 重低音偏高 ({su}%)')
    elif su > 20: sg.append(f'🟢 重低音充足 ({su}%)')
    if ba > 40: sg.append(f'🔴 低音偏高 ({ba}%)')
    elif ba > 25: sg.append(f'🟢 低音适中 ({ba}%)')
    if lm > 30: sg.append(f'🔴 低中频浑浊 ({lm}%)')
    if hm > 25: sg.append(f'🔴 齿音过重 ({hm}%)')
    if hv < 10: sg.append(f'🟡 高频不足 ({hv}%)')
    if cf < 8: sg.append(f'🟡 动态很小 ({cf} dB)')
    elif cf < 18: sg.append(f'🟢 动态适中 ({cf} dB)')
    else: sg.append(f'🟢 动态大 ({cf} dB)')
    return sg

# ==================== 主界面 ====================
def main():
    # 主容器
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 头部
    st.markdown(f'''
    <div class="header-section">
        <div class="logo-container">
            {FLASH_SVG}
            <div class="title-section">
                <h1>FLASH</h1>
                <p>PROFESSIONAL AUDIO ANALYZER</p>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="color: #3b82f6; font-family: 'JetBrains Mono', monospace; font-size: 14px;">v5.0</div>
            <div style="color: #6b7280; font-size: 13px;">Dashboard</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if MISSING_PKGS:
        st.info(f'💡 完整功能：`pip install {" ".join(MISSING_PKGS)}`')

    # 模式选择
    mode = st.radio("分析模式", ["🎵 单轨分析", "🎚️ 参考曲对比"], horizontal=True)

    if mode == "🎵 单轨分析":
        # 文件上传区
        st.markdown('<div class="uploader-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 48px; margin-bottom: 16px;">📁</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #f3f4f6; font-size: 20px; font-weight: 600; margin-bottom: 8px;">拖拽音频文件到此处</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #6b7280; font-size: 14px;">支持 WAV, MP3, FLAC, AIFF 格式</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded = st.file_uploader('', type=['wav', 'mp3', 'flac', 'aiff', 'aif'], label_visibility='collapsed')

        if uploaded is not None:
            if uploaded.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f'❌ 文件过大！请上传小于 {MAX_FILE_SIZE_MB}MB 的文件')
                st.stop()

            # 分析
            with st.spinner(''):
                t0 = time.time()
                res = analyze_audio_cached(uploaded.getvalue(), uploaded.name)
                elapsed = round(time.time() - t0, 1)

            if res is None:
                st.error("分析失败，请安装 librosa")
                st.stop()

            sg = generate_suggestions(res)
            res['suggestions'] = sg

            # 核心指标网格
            st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">🎵</div>
                    <div class="metric-label">BPM</div>
                    <div class="metric-value">{res.get('bpm', 0)}<span class="metric-unit"></span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c2:
                key_disp = f"{res.get('key', '?')}"
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">🎹</div>
                    <div class="metric-label">Key</div>
                    <div class="metric-value">{key_disp}<span class="metric-unit"></span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">🔊</div>
                    <div class="metric-label">LUFS</div>
                    <div class="metric-value">{res['lufs_integrated']}<span class="metric-unit">dB</span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c4:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-label">Dynamic</div>
                    <div class="metric-value">{res['crest_factor_db']}<span class="metric-unit">dB</span></div>
                </div>
                ''', unsafe_allow_html=True)

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">📻</div>
                    <div class="metric-label">Sample Rate</div>
                    <div class="metric-value">{res['sample_rate']/1000:.1f}<span class="metric-unit">kHz</span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c6:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">⏱️</div>
                    <div class="metric-label">Duration</div>
                    <div class="metric-value">{format_duration(res['duration_sec'])}<span class="metric-unit"></span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c7:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-label">Spectral Centroid</div>
                    <div class="metric-value">{res['spectral_centroid']}<span class="metric-unit">Hz</span></div>
                </div>
                ''', unsafe_allow_html=True)
            with c8:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-icon">🔈</div>
                    <div class="metric-label">Channels</div>
                    <div class="metric-value">{res['channels']}<span class="metric-unit"></span></div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # 分析完成提示
            st.markdown(f'''
            <div style="text-align: center; color: #10b981; font-family: 'JetBrains Mono', monospace; margin: 20px 0; padding: 16px; background: rgba(16, 185, 129, 0.1); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3);">
                ✅ 分析完成 · {elapsed}s · True Peak: {res.get('true_peak_db', 0)} dBFS
            </div>
            ''', unsafe_allow_html=True)

            # 频率分布
            st.markdown('<div class="content-section">', unsafe_allow_html=True)
            st.markdown('''
            <div class="section-header">
                <div class="section-icon">📊</div>
                <h2 class="section-title">Frequency Spectrum</h2>
            </div>
            ''', unsafe_allow_html=True)
            
            for k, v in res['frequency'].items():
                pct = v['pct']
                bar_w = min(pct * 2, 100)
                st.markdown(f'''
                <div class="frequency-item">
                    <div class="frequency-header">
                        <div>
                            <span class="frequency-name">{v['label']}</span>
                            <span class="frequency-name-cn">{v['label_cn']}</span>
                        </div>
                        <span class="frequency-percent">{pct}%</span>
                    </div>
                    <div class="frequency-track">
                        <div class="frequency-fill" style="width: {bar_w}%"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # EQ 推荐
            if res.get('eq_suggestions'):
                st.markdown('<div class="content-section">', unsafe_allow_html=True)
                st.markdown('''
                <div class="section-header">
                    <div class="section-icon">🎛️</div>
                    <h2 class="section-title">EQ Recommendations</h2>
                </div>
                ''', unsafe_allow_html=True)
                
                for eq in res['eq_suggestions']:
                    icon = '🔴' if eq['type'] == 'cut' else '🟢'
                    st.markdown(f'''
                    <div class="eq-card">
                        <div class="eq-header">
                            <span class="eq-icon">{icon}</span>
                            <span class="eq-title">{eq['desc']}</span>
                        </div>
                        <div class="eq-reason">{eq['reason']}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # 母带推荐
            if 'mastering' in res:
                st.markdown('<div class="content-section">', unsafe_allow_html=True)
                st.markdown('''
                <div class="section-header">
                    <div class="section-icon">🎚️</div>
                    <h2 class="section-title">Mastering Chain</h2>
                </div>
                ''', unsafe_allow_html=True)
                
                m = res['mastering']
                c = m['compressor']
                l = m['limiter']
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f'''
                    <div style="background: rgba(17, 24, 39, 0.8); border-radius: 12px; padding: 20px; border: 1px solid rgba(59, 130, 246, 0.2);">
                        <div style="color: #3b82f6; font-weight: 700; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace;">COMPRESSOR</div>
                        <div style="color: #9ca3af; font-size: 14px; line-height: 2;">
                        Threshold: <span style="color: #f3f4f6;">{c['threshold']} dB</span><br/>
                        Ratio: <span style="color: #f3f4f6;">{c['ratio']}:1</span><br/>
                        Attack: <span style="color: #f3f4f6;">{c['attack']} ms</span><br/>
                        Release: <span style="color: #f3f4f6;">{c['release']} ms</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                with col_m2:
                    st.markdown(f'''
                    <div style="background: rgba(17, 24, 39, 0.8); border-radius: 12px; padding: 20px; border: 1px solid rgba(139, 92, 246, 0.2);">
                        <div style="color: #8b5cf6; font-weight: 700; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace;">LIMITER</div>
                        <div style="color: #9ca3af; font-size: 14px; line-height: 2;">
                        Threshold: <span style="color: #f3f4f6;">{l['threshold']} dB</span><br/>
                        Ceiling: <span style="color: #f3f4f6;">{l['ceiling']} dB</span><br/>
                        <div style="margin-top: 12px; padding: 12px; background: rgba(139, 92, 246, 0.1); border-radius: 8px;">
                        Target LUFS: <span style="color: #fbbf24; font-weight: 700;">{m['target_lufs']} dB</span><br/>
                        Gain: <span style="color: #fbbf24; font-weight: 700;">{m['gain_needed']:+} dB</span>
                        </div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # 混音建议
            if sg:
                st.markdown('<div class="content-section">', unsafe_allow_html=True)
                st.markdown('''
                <div class="section-header">
                    <div class="section-icon">💡</div>
                    <h2 class="section-title">Mix Insights</h2>
                </div>
                ''', unsafe_allow_html=True)
                
                for i, s in enumerate(sg[:10], 1):
                    st.markdown(f'''
                    <div style="padding: 12px 16px; background: rgba(17, 24, 39, 0.6); border-radius: 8px; margin: 8px 0; border-left: 3px solid #3b82f6; color: #d1d5db;">
                        {i}. {s}
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # 导出报告
            st.markdown('<div style="text-align: center; margin-top: 40px;">', unsafe_allow_html=True)
            report_text = generate_report(res, uploaded.name)
            st.download_button(
                "📥 下载分析报告",
                report_text,
                f"FLASH_{uploaded.name}.txt",
                "text/plain",
                key="download_btn"
            )
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # 参考曲对比模式
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown('''
        <div class="section-header">
            <div class="section-icon">🎚️</div>
            <h2 class="section-title">Reference Track Comparison</h2>
        </div>
        ''', unsafe_allow_html=True)
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.markdown('<div style="color: #9ca3af; margin-bottom: 8px;">Your Mix</div>', unsafe_allow_html=True)
            f1 = st.file_uploader("", type=['wav', 'mp3', 'flac'], key="f1")
        with col_u2:
            st.markdown('<div style="color: #9ca3af; margin-bottom: 8px;">Reference Track</div>', unsafe_allow_html=True)
            f2 = st.file_uploader("", type=['wav', 'mp3', 'flac'], key="f2")

        if f1 and f2:
            with st.spinner(''):
                r1 = analyze_audio_cached(f1.getvalue(), f1.name)
                r2 = analyze_audio_cached(f2.getvalue(), f2.name)

            if r1 and r2:
                st.markdown(f'''
                <div style="text-align: center; color: #10b981; font-family: 'JetBrains Mono', monospace; margin: 20px 0; padding: 16px; background: rgba(16, 185, 129, 0.1); border-radius: 12px;">
                    ✅ 对比分析完成
                </div>
                ''', unsafe_allow_html=True)

                # 参数对比
                compare_items = [
                    ('BPM', r1.get('bpm', 0), r2.get('bpm', 0), ''),
                    ('LUFS', r1['lufs_integrated'], r2['lufs_integrated'], ' dB'),
                    ('Dynamic', r1['crest_factor_db'], r2['crest_factor_db'], ' dB'),
                    ('Spectral', r1['spectral_centroid'], r2['spectral_centroid'], ' Hz'),
                ]

                for label, v1, v2, unit in compare_items:
                    diff = round(v1 - v2, 1) if isinstance(v1, (int, float)) else 0
                    diff_color = "#10b981" if abs(diff) < 2 else ("#f59e0b" if abs(diff) < 5 else "#ef4444")
                    diff_sign = "+" if diff > 0 else ""
                    st.markdown(f'''
                    <div style="display: flex; align-items: center; padding: 16px; margin: 8px 0; background: rgba(17, 24, 39, 0.6); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.15);">
                        <div style="width: 120px; color: #9ca3af; font-weight: 600;">{label}</div>
                        <div style="flex: 1; text-align: center; color: #3b82f6; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{v1}{unit}</div>
                        <div style="width: 60px; text-align: center; color: #4b5563;">vs</div>
                        <div style="flex: 1; text-align: center; color: #8b5cf6; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{v2}{unit}</div>
                        <div style="width: 100px; text-align: center; color: {diff_color}; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 18px;">{diff_sign}{diff}{unit}</div>
                    </div>
                    ''', unsafe_allow_html=True)

                # 频率对比
                st.markdown('<div style="margin-top: 32px;">', unsafe_allow_html=True)
                st.markdown('<div style="color: #f3f4f6; font-weight: 700; margin-bottom: 20px; font-size: 18px;">Frequency Comparison</div>', unsafe_allow_html=True)

                for k, _, _, label_en, label_cn in BANDS_DEF:
                    p1 = r1['frequency'].get(k, {}).get('pct', 0)
                    p2 = r2['frequency'].get(k, {}).get('pct', 0)
                    diff = p1 - p2
                    diff_color = "#ef4444" if diff > 5 else ("#10b981" if diff < -5 else "#6b7280")
                    st.markdown(f'''
                    <div style="margin: 12px 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <div style="color: #d1d5db; font-size: 14px;">
                                {label_en}<span style="color: #6b7280; margin-left: 6px;">{label_cn}</span>
                            </div>
                            <div style="color: {diff_color}; font-family: 'JetBrains Mono', monospace; font-size: 14px;">
                                {diff:+.1f}%
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <div style="flex: 1; height: 10px; background: rgba(17, 24, 39, 0.8); border-radius: 5px; overflow: hidden;">
                                <div style="height: 100%; width: {p1*2}%; background: linear-gradient(90deg, #ef4444, #f59e0b); border-radius: 5px;"></div>
                            </div>
                            <div style="width: 40px; text-align: center; color: #ef4444; font-size: 12px; font-family: 'JetBrains Mono', monospace;">{p1}%</div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center; margin-top: 4px;">
                            <div style="flex: 1; height: 10px; background: rgba(17, 24, 39, 0.8); border-radius: 5px; overflow: hidden;">
                                <div style="height: 100%; width: {p2*2}%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); border-radius: 5px;"></div>
                            </div>
                            <div style="width: 40px; text-align: center; color: #8b5cf6; font-size: 12px; font-family: 'JetBrains Mono', monospace;">{p2}%</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # 差距建议
                st.markdown('<div style="margin-top: 24px;">', unsafe_allow_html=True)
                lufs_diff = r1['lufs_integrated'] - r2['lufs_integrated']
                if lufs_diff < -3:
                    st.info(f"📢 你的歌比参考曲轻 {abs(lufs_diff):.1f} dB")
                elif lufs_diff > 3:
                    st.warning(f"📢 你的歌比参考曲响 {lufs_diff:.1f} dB")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # 页脚
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('''
    <div style="text-align: center; color: #4b5563; font-size: 12px; padding: 40px 0; border-top: 1px solid rgba(59, 130, 246, 0.1); margin-top: 60px;">
        FLASH Audio Analyzer v5.0 · Built with Streamlit
    </div>
    ''', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
