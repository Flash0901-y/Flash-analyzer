"""
FLASH 闪光音频分析器 - Streamlit Web 版
v4.0 — UI 美化版：渐变背景/玻璃态卡片/流畅动效/视觉层次
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
    ('sub_bass', 20, 60, '重低音 20-60Hz'),
    ('bass', 60, 250, '低音 60-250Hz'),
    ('low_mid', 250, 500, '低中频 250-500Hz'),
    ('mid', 500, 2000, '中频 500-2kHz'),
    ('high_mid', 2000, 4000, '高中频 2k-4kHz'),
    ('presence', 4000, 6000, '临场感 4k-6kHz'),
    ('high', 6000, 20000, '高频 6k-20kHz'),
]
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

# ==================== 美化的 CSS 样式 ====================
CUSTOM_CSS = """
<style>
/* ===== 全局背景渐变 ===== */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #0f0c29 100%);
    background-attachment: fixed;
    min-height: 100vh;
}

/* ===== 隐藏默认 Streamlit 元素 ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ===== 卡片式容器 - 玻璃态效果 ===== */
div[data-testid="stMetric"], 
div[data-testid="stMetricValue"],
div[data-testid="stMetricLabel"] {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.2);
}

/* ===== 标题样式 ===== */
h1, h2, h3 {
    font-weight: 700 !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* ===== 按钮美化 ===== */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

/* ===== 文件上传区域美化 ===== */
div[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 2px dashed rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

div[data-testid="stFileUploader"]:hover {
    border-color: rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.08);
}

/* ===== 进度条和 Spinner 美化 ===== */
div[data-testid="stSpinner"] {
    color: #667eea !important;
}

/* ===== 成功/警告/错误消息框美化 ===== */
div[data-testid="stSuccessMessage"],
div[data-testid="stWarningMessage"],
div[data-testid="stInfoMessage"],
div[data-testid="stErrorMessage"] {
    backdrop-filter: blur(10px);
    border-radius: 8px;
    border: none;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* ===== 列间距优化 ===== */
div[data-testid="stColumn"] {
    padding: 0 8px;
}

/* ===== 自定义动画 - 浮动效果 ===== */
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.flash-icon {
    animation: float 3s ease-in-out infinite;
    display: inline-block;
}

/* ===== 淡入动画 ===== */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.6s ease-out forwards;
}

/* ===== 频率条美化 ===== */
.frequency-bar {
    background: linear-gradient(90deg, #ff6b6b, #ffd93d, #4ecdc4);
    border-radius: 8px;
    transition: width 0.5s ease;
    position: relative;
    overflow: hidden;
}

.frequency-bar::after {
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

/* ===== 音频播放器美化 ===== */
audio::-webkit-media-controls-panel {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
}

/* ===== 分隔线美化 ===== */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    margin: 20px 0;
}

/* ===== 下载按钮特殊样式 ===== */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
    box-shadow: 0 4px 15px rgba(0, 198, 255, 0.4);
}

div[data-testid="stDownloadButton"] > button:hover {
    box-shadow: 0 6px 20px rgba(0, 198, 255, 0.6);
}

/* ===== Radio 按钮美化 ===== */
div[data-testid="stRadio"] label {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.3s ease;
}

div[data-testid="stRadio"] label:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
}

div[data-testid="stRadio"] input:checked + span {
    color: #667eea;
    font-weight: 600;
}
</style>
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
    """4x 过采样 True Peak 检测（三次样条插值）"""
    from scipy.interpolate import interp1d
    n = len(y)
    x_orig = np.arange(n)
    x_upsampled = np.linspace(0, n - 1, n * 4)
    f = interp1d(x_orig, y, kind='cubic', bounds_error=False, fill_value=0)
    y_upsampled = f(x_upsampled)
    true_peak = float(np.max(np.abs(y_upsampled)))
    true_peak_db = round(20 * np.log10(true_peak + 1e-10), 2)
    return true_peak, true_peak_db


# ==================== 分析报告生成 ====================
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
        if st_info.get('mono_issues'):
            lines.append("")
            lines.append("  ⚠️ Mono 兼容性问题:")
            for iss in st_info['mono_issues']:
                lines.append(f"     {iss['band']}: 相关性 {iss['corr']}")
        if st_info.get('phase_warnings'):
            lines.append("")
            for w in st_info['phase_warnings']:
                lines.append(f"  {w}")
        lines.append("")

    if 'eq_suggestions' in res and res['eq_suggestions']:
        lines.append("【EQ 精确参数推荐】")
        for i, eq in enumerate(res['eq_suggestions'], 1):
            lines.append(f"  {i}. {eq['desc']} → {eq['reason']}")
        lines.append("")

    if 'mastering' in res:
        m = res['mastering']
        lines.append("【母带参数推荐】")
        lines.append(f"  目标 LUFS:     {m['target_lufs']} dB (需要增益 {m['gain_needed']:+} dB)")
        c = m['compressor']
        lines.append(f"  压缩器：阈值 {c['threshold']}dB / 比率 {c['ratio']}:1 / 攻击 {c['attack']}ms / 释放 {c['release']}ms")
        lines.append(f"                ({c['note']})")
        l = m['limiter']
        lines.append(f"  限制器：阈值 {l['threshold']}dB / 天花板 {l['ceiling']}dB")
        lines.append(f"  音色：{m['tone']}")
        lines.append("")

    lines.append("【混音建议】")
    sg = res.get('suggestions', [])
    for i, s in enumerate(sg[:10], 1):
        lines.append(f"  {i}. {s}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("         FLASH 闪光音频分析器 v4.0")
    lines.append("=" * 60)
    return "\n".join(lines)


# ==================== 页面配置 ====================
st.set_page_config(
    page_title='FLASH 闪光音频分析器',
    page_icon='⚡',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# 注入自定义 CSS
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
    """频率波段能量分析 — 使用 float64 避免精度显示问题"""
    import librosa
    D = librosa.stft(y, n_fft=4096)
    mag = np.abs(D).astype(np.float64)
    fr = librosa.fft_frequencies(sr=sr, n_fft=4096)
    total_energy = float(np.sum(mag ** 2))

    freq_bands = {}
    for k, lo, hi, la in BANDS_DEF:
        msk = (fr >= lo) & (fr < hi)
        energy = float(np.sum(mag[msk] ** 2))
        pct = round(energy / total_energy * 100, 1) if total_energy > 0 else 0
        freq_bands[k] = {'label': la, 'pct': pct}

    return freq_bands, mag, fr


def analyze_dynamics(y, sr):
    """动态分析 — 修正 Crest Factor = peak / overall_rms，增加 True Peak"""
    import librosa

    peak = float(np.max(np.abs(y)))
    overall_rms = float(np.sqrt(np.mean(y ** 2)))
    crest_db = round(20 * np.log10(peak / overall_rms), 1) if overall_rms > 0 else 0

    avg_rms = float(np.mean(librosa.feature.rms(y=y)[0]))
    sc = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))

    # LUFS
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

    # True Peak（4x 过采样）
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
    """专业版立体声 + 相位分析 — 使用 float64 避免精度问题"""
    if y_stereo.ndim <= 1 or y_stereo.shape[0] < 2:
        return None

    import librosa
    left = y_stereo[0]
    right = y_stereo[1]

    corr = float(np.corrcoef(left, right)[0, 1])
    left_rms = round(float(np.sqrt(np.mean(left ** 2))), 4)
    right_rms = round(float(np.sqrt(np.mean(right ** 2))), 4)

    D_l = librosa.stft(left, n_fft=4096)
    D_r = librosa.stft(right, n_fft=4096)
    mag_l = np.abs(D_l).astype(np.float64)
    mag_r = np.abs(D_r).astype(np.float64)
    fr = librosa.fft_frequencies(sr=sr, n_fft=4096)

    band_corrs = {}
    mono_issues = []

    for bk, blo, bhi, bla in BANDS_DEF:
        bmsk = (fr >= blo) & (fr < bhi)
        if np.sum(bmsk) > 1:
            bl = np.sum(mag_l[bmsk], axis=0)
            br = np.sum(mag_r[bmsk], axis=0)
            if np.std(bl) > 1e-10 and np.std(br) > 1e-10:
                bcorr = round(float(np.corrcoef(bl, br)[0, 1]), 2)
                band_corrs[bk] = {
                    'label': bla,
                    'corr': bcorr,
                    'lo': blo,
                    'hi': bhi
                }
                if bhi <= 250 and bcorr < 0.7:
                    mono_issues.append({
                        'band': bla,
                        'corr': bcorr,
                        'severity': 'high' if bcorr < 0.5 else 'medium'
                    })

    phase_issues = []
    if corr < 0:
        phase_issues.append("❌ 全局反相！检查左右声道接线")
    elif corr < 0.2:
        phase_issues.append("⚠️ 立体声过宽，Mono 兼容性差")

    return {
        'correlation': corr,
        'left_rms': left_rms,
        'right_rms': right_rms,
        'band_correlations': band_corrs,
        'mono_issues': mono_issues,
        'phase_warnings': phase_issues
    }


def generate_eq_suggestions(freq_bands):
    """精确 EQ 参数推荐（移除无用参数）"""
    suggestions = []

    su = freq_bands.get('sub_bass', {}).get('pct', 0)
    ba = freq_bands.get('bass', {}).get('pct', 0)
    lm = freq_bands.get('low_mid', {}).get('pct', 0)
    md = freq_bands.get('mid', {}).get('pct', 0)
    hm = freq_bands.get('high_mid', {}).get('pct', 0)
    pr = freq_bands.get('presence', {}).get('pct', 0)
    hv = freq_bands.get('high', {}).get('pct', 0)

    if lm > 25:
        suggestions.append({
            'type': 'cut', 'freq': 300, 'q': 1.4, 'gain': -2,
            'reason': f'低中频浑浊 ({lm}%)',
            'desc': '300Hz Q1.4 衰减 2dB'
        })
    if hm > 20:
        suggestions.append({
            'type': 'cut', 'freq': 3500, 'q': 2.0, 'gain': -1.5,
            'reason': f'齿音过重 ({hm}%)',
            'desc': '3.5kHz Q2.0 衰减 1.5dB (De-esser)'
        })
    if hv < 8:
        suggestions.append({
            'type': 'boost', 'freq': 12000, 'q': 0.7, 'gain': 1.5,
            'reason': '高频空气感不足',
            'desc': '12kHz Shelf 提升 1.5dB'
        })
    if ba > 35:
        suggestions.append({
            'type': 'cut', 'freq': 120, 'q': 1.0, 'gain': -2,
            'reason': f'低音过多 ({ba}%)',
            'desc': '120Hz Q1.0 衰减 2dB'
        })
    if md > 55:
        suggestions.append({
            'type': 'cut', 'freq': 1000, 'q': 1.4, 'gain': -1.5,
            'reason': f'中频突出 ({md}%)',
            'desc': '1kHz Q1.4 衰减 1.5dB'
        })
    if pr < 8:
        suggestions.append({
            'type': 'boost', 'freq': 5000, 'q': 1.0, 'gain': 1,
            'reason': '缺乏临场感',
            'desc': '5kHz Q1.0 提升 1dB'
        })

    return suggestions


def generate_mastering_suggestions(lufs, crest, sc):
    """母带参数推荐"""
    if lufs < -16:
        target_lufs = -14
    elif lufs < -10:
        target_lufs = -10
    else:
        target_lufs = lufs

    if crest > 14:
        compressor = {
            'threshold': -20, 'ratio': 1.5, 'attack': 30, 'release': 200,
            'note': '动态大，温和压缩'
        }
    elif crest > 8:
        compressor = {
            'threshold': -18, 'ratio': 2.0, 'attack': 20, 'release': 150,
            'note': '标准流行设置'
        }
    else:
        compressor = {
            'threshold': -15, 'ratio': 2.5, 'attack': 15, 'release': 100,
            'note': '动态小，谨慎压缩'
        }

    if sc < 1500:
        tone = '偏暗，建议高频提升'
    elif sc < 2500:
        tone = '平衡'
    else:
        tone = '偏亮，注意齿音'

    return {
        'target_lufs': target_lufs,
        'gain_needed': round(target_lufs - lufs, 1),
        'compressor': compressor,
        'limiter': {'threshold': -0.3, 'ceiling': -0.1, 'release': 100, 'note': '标准母带限制'},
        'tone': tone
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
    md = fq.get('mid', {}).get('pct', 0)
    hm = fq.get('high_mid', {}).get('pct', 0)
    pr = fq.get('presence', {}).get('pct', 0)
    hv = fq.get('high', {}).get('pct', 0)
    cf = res.get('crest_factor_db', 0)
    lufs = res.get('lufs_integrated', 0)

    if su > 35:
        sg.append(f'🔴 重低音偏高 ({su}%)，40Hz 以下高通')
    elif su > 20:
        sg.append(f'🟢 重低音充足 ({su}%)')
    elif su > 5:
        sg.append(f'🟡 重低音较少 ({su}%)')

    if ba > 40:
        sg.append(f'🔴 低音偏高 ({ba}%)，Kick/Bass 冲突')
    elif ba > 25:
        sg.append(f'🟢 低音适中 ({ba}%)')
    elif ba > 5:
        sg.append(f'🟡 低音偏少 ({ba}%)')

    if lm > 30:
        sg.append(f'🔴 低中频浑浊 ({lm}%)，250-500Hz 衰减')
    elif lm > 15:
        sg.append(f'🟢 低中频适中 ({lm}%)')

    if md > 70:
        sg.append(f'🔴 中频过高 ({md}%)')
    elif md > 50:
        sg.append(f'🟡 中频偏高 ({md}%)')
    elif md > 25:
        sg.append(f'🟢 中频适中 ({md}%)')

    if hm > 25:
        sg.append(f'🔴 齿音过重 ({hm}%)')
    if pr > 15:
        sg.append(f'🟢 临场感较好 ({pr}%)')

    if hv > 25:
        sg.append(f'🟡 高频偏高 ({hv}%)')
    elif hv > 10:
        sg.append(f'🟢 高频适中 ({hv}%)')
    else:
        sg.append(f'🟡 高频不足 ({hv}%)，缺少空气感')

    if cf < 8:
        sg.append(f'🟡 动态很小 ({cf} dB)，过度压缩')
    elif cf < 12:
        sg.append(f'🟡 动态偏小 ({cf} dB)')
    elif cf < 18:
        sg.append(f'🟢 动态适中 ({cf} dB)')
    else:
        sg.append(f'🟢 动态大 ({cf} dB)')

    if lufs < -20:
        sg.append(f'🟢 LUFS({lufs}dB) 适合古典')
    elif lufs < -14:
        sg.append(f'🟢 LUFS({lufs}dB) Spotify 标准')
    elif lufs < -8:
        sg.append(f'🟡 LUFS({lufs}dB) 适合 EDM/流行')
    else:
        sg.append(f'🔴 LUFS({lufs}dB) 过高，小心削波')

    if 'stereo' in res and res['stereo']:
        st = res['stereo']
        for iss in st.get('mono_issues', []):
            sg.append(f"⚠️ {iss['band']} 立体声过宽，Mono 播放会消失！")
        for w in st.get('phase_warnings', []):
            sg.append(w)

    return sg


# ==================== 主界面 ====================
def main():
    # 美化标题区域
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:64px;margin:0" class="flash-icon">⚡</p>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center;font-size:48px;margin:10px 0">FLASH 闪光音频分析器</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;font-size:18px;margin-bottom:30px">🎵 专业音频分析 · BPM/调性/频率/EQ 推荐/母带参数 · 参考曲对比</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if MISSING_PKGS:
        st.info(f'💡 完整功能：`pip install {" ".join(MISSING_PKGS)}`')

    mode = st.radio("分析模式", ["🎵 单轨分析", "🎚️ 参考曲对比"], horizontal=True)

    if mode == "🎵 单轨分析":
        uploaded = st.file_uploader('拖拽音频文件到此处', type=['wav', 'mp3', 'flac', 'aiff', 'aif'])

        if uploaded is not None:
            if uploaded.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f'❌ 文件过大！请上传小于 {MAX_FILE_SIZE_MB}MB 的文件')
                st.stop()

            st.audio(uploaded)

            with st.spinner('🎧 正在专业分析...'):
                t0 = time.time()
                res = analyze_audio_cached(uploaded.getvalue(), uploaded.name)
                elapsed = round(time.time() - t0, 1)

            if res is None:
                st.error("分析失败，请安装 librosa")
                st.stop()

            sg = generate_suggestions(res)
            res['suggestions'] = sg

            # ===== 核心指标 =====
            st.markdown('---')
            st.markdown('<div class="fade-in">', unsafe_allow_html=True)
            st.markdown('<h2 style="font-size:28px;margin-bottom:20px">📊 核心参数</h2>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric('🎵 BPM', f"{res.get('bpm', 0)}")
            with c2:
                key_disp = f"{res.get('key', '?')} ({res.get('key_confidence', 0):.0%})"
                st.metric('🎹 调性', key_disp)
            with c3:
                lufs_label = f"{res['lufs_integrated']} dB{' ≈' if res.get('lufs_estimated') else ''}"
                st.metric('🔊 LUFS', lufs_label)
            with c4:
                st.metric('🎯 Crest', f"{res['crest_factor_db']} dB")

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                st.metric('📻 采样率', f"{res['sample_rate']/1000:.1f}k")
            with c6:
                st.metric('⏱️ 时长', format_duration(res['duration_sec']))
            with c7:
                st.metric('🎯 质心', f"{res['spectral_centroid']} Hz")
            with c8:
                st.metric('🔈 声道', res['channels'])

            # True Peak 额外显示
            if 'true_peak_db' in res:
                st.caption(f'✅ 专业分析完成 · {elapsed}s  |  True Peak: {res["true_peak_db"]} dBFS')
            st.markdown('</div>', unsafe_allow_html=True)

            # ===== 频率分布 =====
            st.markdown('---')
            st.markdown('<div class="fade-in">', unsafe_allow_html=True)
            st.markdown('<h2 style="font-size:28px;margin-bottom:20px">📈 频率分布</h2>', unsafe_allow_html=True)
            for k, v in res['frequency'].items():
                pct = v['pct']
                bar_w = min(pct * 2, 100)
                st.markdown(f'''
                <div style="margin:8px 0" class="fade-in">
                    <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px">
                        <span style="font-weight:500">{v["label"]}</span>
                        <span style="font-weight:bold;color:#ffd93d">{pct}%</span>
                    </div>
                    <div style="height:20px;background:rgba(255,255,255,0.05);border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.1)">
                        <div class="frequency-bar" style="height:100%;width:{bar_w}%"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ===== EQ 参数推荐 =====
            if res.get('eq_suggestions'):
                st.markdown('---')
                st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                st.markdown('<h2 style="font-size:28px;margin-bottom:20px">🎛️ EQ 精确参数推荐</h2>', unsafe_allow_html=True)
                for eq in res['eq_suggestions']:
                    icon = '🔴' if eq['type'] == 'cut' else '🟢'
                    st.markdown(f'''
                    <div style="padding:16px 20px;background:linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));border-radius:12px;margin:8px 0;border-left:4px solid #ffd93d;transition:all 0.3s ease" 
                         onmouseover="this.style.transform='translateX(8px)';this.style.boxShadow='0 4px 20px rgba(255,217,61,0.3)'" 
                         onmouseout="this.style.transform='translateX(0)';this.style.boxShadow='none'">
                        <div style="font-weight:bold;font-size:16px">{icon} {eq['desc']}</div>
                        <div style="font-size:14px;color:#888;margin-top:6px">{eq['reason']}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ===== 母带推荐 =====
            if 'mastering' in res:
                st.markdown('---')
                st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                st.markdown('<h2 style="font-size:28px;margin-bottom:20px">🎚️ 母带参数推荐</h2>', unsafe_allow_html=True)
                m = res['mastering']
                c = m['compressor']
                l = m['limiter']

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f'''
                    <div style="padding:20px;background:rgba(255,255,255,0.05);border-radius:12px;border:1px solid rgba(255,255,255,0.1)">
                    <h3 style="font-size:20px;margin-bottom:12px;color:#667eea">压缩器 Compressor</h3>
                    <div style="font-size:14px;line-height:1.8">
                    阈值：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{c['threshold']} dB</code><br/>
                    比率：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{c['ratio']}:1</code><br/>
                    攻击：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{c['attack']} ms</code><br/>
                    释放：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{c['release']} ms</code><br/>
                    <em style="color:#888">{c['note']}</em>
                    </div>
                    </div>
                    ''', unsafe_allow_html=True)
                with col_m2:
                    st.markdown(f'''
                    <div style="padding:20px;background:rgba(255,255,255,0.05);border-radius:12px;border:1px solid rgba(255,255,255,0.1)">
                    <h3 style="font-size:20px;margin-bottom:12px;color:#00c6ff">限制器 Limiter</h3>
                    <div style="font-size:14px;line-height:1.8">
                    阈值：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{l['threshold']} dB</code><br/>
                    天花板：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{l['ceiling']} dB</code><br/>
                    释放：<code style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px">{l['release']} ms</code><br/>
                    <div style="margin-top:12px;padding:12px;background:rgba(0,198,255,0.1);border-radius:8px;border-left:3px solid #00c6ff">
                    <strong>目标 LUFS: {m['target_lufs']} dB</strong><br/>
                    需要增益：{m['gain_needed']:+} dB
                    </div>
                    </div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ===== 立体声分析 =====
            if 'stereo' in res and res['stereo']:
                st.markdown('---')
                st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                st.markdown('<h2 style="font-size:28px;margin-bottom:20px">🎧 立体声场 & 相位检测</h2>', unsafe_allow_html=True)
                st_info = res['stereo']
                corr = st_info['correlation']

                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("相关性", f"{corr:.3f}")
                with sc2:
                    st.metric("左 RMS", st_info['left_rms'])
                with sc3:
                    st.metric("右 RMS", st_info['right_rms'])

                corr_bar = round((corr + 1) * 50, 1)
                corr_color = "#00cc66" if corr > 0.3 else ("#ffd93d" if corr > 0 else "#ff4444")
                status = "✅ 正常" if corr > 0.3 else ("⚠️ 接近 Mono" if corr > 0 else "❌ 反相!")

                st.markdown(f'''
                <div style="margin:16px 0;padding:16px;background:rgba(255,255,255,0.05);border-radius:12px;border:1px solid rgba(255,255,255,0.1)">
                    <div style="display:flex;justify-content:space-between;font-size:12px;color:#666;margin-bottom:8px">
                        <span>反相 -1</span><span>Mono 0</span><span>立体声 +1</span>
                    </div>
                    <div style="height:20px;background:rgba(0,0,0,0.3);border-radius:10px;position:relative;overflow:hidden">
                        <div style="position:absolute;left:{corr_bar}%;width:4px;height:100%;background:{corr_color};border-radius:2px;box-shadow:0 0 10px {corr_color}"></div>
                        <div style="position:absolute;left:50%;width:1px;height:100%;background:#444"></div>
                    </div>
                    <p style="font-size:14px;margin-top:12px;font-weight:bold">{status}</p>
                </div>
                ''', unsafe_allow_html=True)

                if st_info.get('mono_issues'):
                    st.error("⚠️ **Mono 兼容性警告 - 以下频段立体声过宽**")
                    for iss in st_info['mono_issues']:
                        sev = "🔴 严重" if iss['severity'] == 'high' else "🟡 中等"
                        st.warning(f"{sev} {iss['band']}: 相关性仅 {iss['corr']} —— 手机单声道播放时音量会大幅下降！建议 Mono 兼容检查")
                st.markdown('</div>', unsafe_allow_html=True)

            # ===== 混音建议 =====
            if sg:
                st.markdown('---')
                st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                st.markdown('<h2 style="font-size:28px;margin-bottom:20px">💡 混音建议</h2>', unsafe_allow_html=True)
                for i, s in enumerate(sg[:10], 1):
                    st.markdown(f'<div style="padding:12px 16px;background:rgba(255,255,255,0.05);border-radius:8px;margin:6px 0;border-left:3px solid #667eea;transition:all 0.3s ease" onmouseover="this.style.background=\'rgba(255,255,255,0.08)\';this.style.transform=\'translateX(4px)\'" onmouseout="this.style.background=\'rgba(255,255,255,0.05)\';this.style.transform=\'translateX(0)\'">{i}. {s}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ===== 导出报告 =====
            st.markdown('---')
            report_text = generate_report(res, uploaded.name)
            st.download_button(
                "📥 下载专业分析报告",
                report_text,
                f"FLASH_{uploaded.name}.txt",
                "text/plain"
            )

    else:
        # ========== 参考曲对比模式 ==========
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.markdown('<h2 style="font-size:28px;margin-bottom:20px">🎚️ 参考曲对比分析</h2>', unsafe_allow_html=True)
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            f1 = st.file_uploader("🎵 你的混音", type=['wav', 'mp3', 'flac'])
        with col_u2:
            f2 = st.file_uploader("🎯 参考曲 (商业发行)", type=['wav', 'mp3', 'flac'])

        if f1 and f2:
            with st.spinner('🎧 正在对比分析...'):
                r1 = analyze_audio_cached(f1.getvalue(), f1.name)
                r2 = analyze_audio_cached(f2.getvalue(), f2.name)

            if r1 and r2:
                st.success("✅ 对比分析完成")

                # 参数对比表
                st.markdown('---')
                st.markdown('<h3 style="font-size:24px;margin-bottom:20px">📊 参数对比</h3>', unsafe_allow_html=True)

                compare_items = [
                    ('BPM', r1.get('bpm', 0), r2.get('bpm', 0), ''),
                    ('LUFS (响度)', r1['lufs_integrated'], r2['lufs_integrated'], ' dB'),
                    ('动态范围', r1['crest_factor_db'], r2['crest_factor_db'], ' dB'),
                    ('频谱质心', r1['spectral_centroid'], r2['spectral_centroid'], ' Hz'),
                ]

                for label, v1, v2, unit in compare_items:
                    diff = round(v1 - v2, 1) if isinstance(v1, (int, float)) else 0
                    diff_color = "#00cc66" if abs(diff) < 2 else ("#ffd93d" if abs(diff) < 5 else "#ff4444")
                    diff_sign = "+" if diff > 0 else ""

                    st.markdown(f'''
                    <div style="display:flex;align-items:center;padding:12px;margin:8px 0;background:rgba(255,255,255,0.05);border-radius:8px;border:1px solid rgba(255,255,255,0.1);transition:all 0.3s ease" onmouseover="this.style.background=\'rgba(255,255,255,0.08)\'">
                        <div style="width:140px;font-weight:bold">{label}</div>
                        <div style="width:100px;text-align:center;color:#667eea">{v1}{unit}</div>
                        <div style="width:30px;text-align:center;color:#666;font-size:12px">vs</div>
                        <div style="width:100px;text-align:center;color:#00c6ff">{v2}{unit}</div>
                        <div style="width:100px;text-align:center;color:{diff_color};font-weight:bold;font-size:16px">
                            {diff_sign}{diff}{unit}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                # 频率对比
                st.markdown('---')
                st.markdown('<h3 style="font-size:24px;margin-bottom:20px">📈 频率分布对比</h3>', unsafe_allow_html=True)

                for k, _, _, label in BANDS_DEF:
                    p1 = r1['frequency'].get(k, {}).get('pct', 0)
                    p2 = r2['frequency'].get(k, {}).get('pct', 0)
                    diff = p1 - p2

                    st.markdown(f'''
                    <div style="margin:12px 0">
                        <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px">
                            <span style="font-weight:500">{label}</span>
                            <span>你的：<strong style="color:#ff6b6b">{p1}%</strong> / 参考：<strong style="color:#4ecdc4">{p2}%</strong> 
                                <span style="color:{"#ff6b6b" if diff>5 else "#00cc66" if diff<-5 else "#888"}">
                                    ({diff:+.1f}%)
                                </span>
                            </span>
                        </div>
                        <div style="display:flex;gap:8px">
                            <div style="flex:1;height:24px;background:rgba(255,255,255,0.05);border-radius:12px;overflow:hidden;border:1px solid rgba(255,255,255,0.1)">
                                <div style="height:100%;width:{p1*2}%;background:linear-gradient(90deg,#ff6b6b,#ff8e8e);border-radius:12px;transition:width 0.5s ease"></div>
                            </div>
                            <div style="flex:1;height:24px;background:rgba(255,255,255,0.05);border-radius:12px;overflow:hidden;border:1px solid rgba(255,255,255,0.1)">
                                <div style="height:100%;width:{p2*2}%;background:linear-gradient(90deg,#4ecdc4,#44dbd1);border-radius:12px;transition:width 0.5s ease"></div>
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;color:#666;margin-top:4px">
                            <span>🔴 你的混音</span><span>🔵 参考曲</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                # 差距建议
                st.markdown('---')
                st.markdown('<h3 style="font-size:24px;margin-bottom:20px">🎯 差距分析建议</h3>', unsafe_allow_html=True)

                lufs_diff = r1['lufs_integrated'] - r2['lufs_integrated']
                if lufs_diff < -3:
                    st.info(f"📢 你的歌比参考曲轻 {abs(lufs_diff):.1f} dB —— 母带可以再提升响度")
                elif lufs_diff > 3:
                    st.warning(f"📢 你的歌比参考曲响 {lufs_diff:.1f} dB —— 注意不要过度压缩")

                for k, _, _, label in BANDS_DEF:
                    p1 = r1['frequency'].get(k, {}).get('pct', 0)
                    p2 = r2['frequency'].get(k, {}).get('pct', 0)
                    if p1 - p2 > 10:
                        st.warning(f"⚠️ {label}: 你的歌比参考曲多 {p1-p2:.1f}% —— 考虑衰减")
                    elif p2 - p1 > 10:
                        st.info(f"💡 {label}: 参考曲比你多 {p2-p1:.1f}% —— 可以提升")
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<p style="text-align:center;color:#555;font-size:12px;margin-top:60px">FLASH 闪光音频分析器 v4.0 ✨</p>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
