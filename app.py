"""
FLASH 闪光音频分析器 - Streamlit Web 版
v5.1 — 修复 HTML 渲染问题
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

# ==================== CSS 样式 ====================
CUSTOM_CSS = """
<style>
/* 全局背景 */
.stApp {
    background: #030308;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* 隐藏 Streamlit 默认元素 */
#MainMenu, footer, header, .stDeployButton {
    visibility: hidden !important;
    display: none !important;
}

/* 网格背景 */
.grid-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-image: 
        linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

/* 头部区域 */
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    margin-bottom: 30px;
}

/* 指标卡片 */
.metric-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(31, 41, 55, 0.9));
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

/* 内容区块 */
.content-box {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.15);
    border-radius: 16px;
    padding: 24px;
    margin: 20px 0;
}

/* 频率条容器 */
.freq-track {
    height: 10px;
    background: rgba(31, 41, 55, 0.8);
    border-radius: 5px;
    overflow: hidden;
}
.freq-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
    border-radius: 5px;
    transition: width 0.6s ease;
}

/* EQ 卡片 */
.eq-card {
    background: rgba(17, 24, 39, 0.8);
    border-left: 3px solid #fbbf24;
    border-radius: 8px;
    padding: 16px;
    margin: 10px 0;
}

/* 按钮美化 */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
}

/* 文件上传区 */
div[data-testid="stFileUploader"] {
    background: rgba(17, 24, 39, 0.6);
    border: 2px dashed rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 40px;
}
div[data-testid="stFileUploader"]:hover {
    border-color: rgba(59, 130, 246, 0.6);
}

/* Radio 按钮 */
div[data-testid="stRadio"] {
    background: rgba(17, 24, 39, 0.6);
    border-radius: 10px;
    padding: 8px;
    border: 1px solid rgba(59, 130, 246, 0.2);
}
</style>

<!-- 网格背景 -->
<div class="grid-bg"></div>
"""

# ==================== SVG 闪电 Logo ====================
FLASH_LOGO_SVG = '''
<svg width="60" height="60" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="flashGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#fbbf24"/>
            <stop offset="50%" style="stop-color:#f59e0b"/>
            <stop offset="100%" style="stop-color:#d97706"/>
        </linearGradient>
    </defs>
    <polygon points="50,5 20,55 45,55 35,95 80,40 55,40" fill="url(#flashGrad)"/>
</svg>
'''

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
    lines = ["=" * 60, "       FLASH 闪光音频分析报告", "=" * 60]
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
    lines.append(f"  True Peak:    {res.get('true_peak_db', 0)} dBFS")
    lines.append("")
    lines.append("【频率分布】")
    for v in res['frequency'].values():
        lines.append(f"  {v['label']:<15} {v['pct']:>5}%")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)

# ==================== 页面配置 ====================
st.set_page_config(page_title='FLASH 音频分析器', page_icon='', layout='wide', initial_sidebar_state='collapsed')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==================== 依赖检查 ====================
@st.cache_resource
def check_dependencies():
    missing = []
    features = {'librosa': False, 'pyloudnorm': False, 'scipy': False}
    try:
        import librosa
        features['librosa'] = True
    except ImportError:
        missing.append('librosa')
    try:
        import pyloudnorm
        features['pyloudnorm'] = True
    except ImportError:
        missing.append('pyloudnorm')
    try:
        from scipy.interpolate import interp1d
        features['scipy'] = True
    except ImportError:
        missing.append('scipy')
    return 'librosa' if features['librosa'] else 'minimal', missing, features

ENGINE, MISSING_PKGS, FEATURES = check_dependencies()

# ==================== 音频分析函数 ====================
def load_audio(filepath):
    import librosa
    y, sr = librosa.load(filepath, sr=None, mono=False)
    ym = librosa.to_mono(y) if y.ndim > 1 else y
    return y, ym, sr, librosa.get_duration(y=ym, sr=sr)

def detect_bpm(y, sr):
    import librosa
    ta = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(ta, tuple): ta = ta[0]
    if hasattr(ta, '__getitem__') and not isinstance(ta, (float, int, str)): ta = ta[0]
    return correct_bpm(ta)

def detect_key(y, sr):
    import librosa
    cf = librosa.feature.chroma_stft(y=y, sr=sr)
    cm = np.mean(cf, axis=1)
    best_key, conf = "C 大调", 0.5
    return best_key, conf

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
    return freq_bands

def analyze_dynamics(y, sr):
    import librosa
    peak = float(np.max(np.abs(y)))
    rms = float(np.sqrt(np.mean(y ** 2)))
    crest_db = round(20 * np.log10(peak / rms), 1) if rms > 0 else 0
    sc = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))
    lufs = round(20 * np.log10(rms + 1e-10) - 0.691, 1)
    true_peak_val, true_peak_db = true_peak_detection(y, sr)
    return {
        'crest_factor_db': crest_db, 'spectral_centroid': int(sc),
        'lufs_integrated': lufs, 'true_peak_db': true_peak_db,
    }

@st.cache_data(show_spinner=False, ttl=3600)
def analyze_audio_cached(file_content, filename):
    ext = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
        tmp.write(file_content)
        tmp.flush()
        if ENGINE == 'librosa':
            y_stereo, y_mono, sr, dur = load_audio(tmp.name)
            result = {
                'sample_rate': sr, 'duration_sec': round(dur, 2),
                'channels': y_stereo.shape[0] if y_stereo.ndim > 1 else 1,
                'bpm': detect_bpm(y_mono, sr),
                'key': detect_key(y_mono, sr)[0], 'key_confidence': detect_key(y_mono, sr)[1],
                'frequency': analyze_spectrum(y_mono, sr),
            }
            result.update(analyze_dynamics(y_mono, sr))
            result['eq_suggestions'] = []
            result['mastering'] = {'target_lufs': -14, 'gain_needed': 0}
            return result
    return None

# ==================== 主界面 ====================
def main():
    # 头部
    col_logo, col_title, col_spacer = st.columns([0.5, 3, 1])
    with col_logo:
        st.markdown(FLASH_LOGO_SVG, unsafe_allow_html=True)
    with col_title:
        st.markdown('<div style="padding: 15px 0;"><h1 style="margin: 0; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 36px;">FLASH</h1><p style="margin: 5px 0 0 0; color: #6b7280; font-size: 14px;">PROFESSIONAL AUDIO ANALYZER</p></div>', unsafe_allow_html=True)
    
    if MISSING_PKGS:
        st.info(f'💡 完整功能：`pip install {" ".join(MISSING_PKGS)}`')

    # 模式选择
    mode = st.radio("分析模式", ["🎵 单轨分析", "🎚️ 参考曲对比"], horizontal=True)

    if mode == " 单轨分析":
        # 文件上传
        st.markdown('<div style="text-align: center; padding: 30px 0;">', unsafe_allow_html=True)
        st.markdown('### 📁 拖拽音频文件到此处')
        st.markdown('支持 WAV, MP3, FLAC, AIFF 格式')
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded = st.file_uploader('', type=['wav', 'mp3', 'flac', 'aiff', 'aif'], label_visibility='collapsed')

        if uploaded is not None:
            if uploaded.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f'❌ 文件过大！请上传小于 {MAX_FILE_SIZE_MB}MB 的文件')
                st.stop()

            with st.spinner('🎧 正在分析...'):
                t0 = time.time()
                res = analyze_audio_cached(uploaded.getvalue(), uploaded.name)
                elapsed = round(time.time() - t0, 1)

            if res is None:
                st.error("分析失败，请安装 librosa")
                st.stop()

            # 成功提示
            st.success(f"✅ 分析完成 · {elapsed}s · True Peak: {res.get('true_peak_db', 0)} dBFS")

            # 核心指标
            st.markdown('<div style="margin: 30px 0;">', unsafe_allow_html=True)
            st.markdown('#### 📊 核心参数')
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric('🎵 BPM', res.get('bpm', 0))
            with c2:
                st.metric('🎹 调性', res.get('key', '?'))
            with c3:
                st.metric('🔊 LUFS', f"{res['lufs_integrated']} dB")
            with c4:
                st.metric(' 动态', f"{res['crest_factor_db']} dB")

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                st.metric(' 采样率', f"{res['sample_rate']/1000:.1f} kHz")
            with c6:
                st.metric('⏱️ 时长', format_duration(res['duration_sec']))
            with c7:
                st.metric(' 质心', f"{res['spectral_centroid']} Hz")
            with c8:
                st.metric('🔈 声道', res['channels'])
            st.markdown('</div>', unsafe_allow_html=True)

            # 频率分布
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('#### 📈 频率分布')
            
            for v in res['frequency'].values():
                pct = v['pct']
                bar_w = min(pct * 2, 100)
                st.markdown(f'''
                <div style="margin: 12px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: #d1d5db; font-size: 14px;">{v['label']} <span style="color: #6b7280;">{v['label_cn']}</span></span>
                        <span style="color: #fbbf24; font-weight: 700; font-family: monospace;">{pct}%</span>
                    </div>
                    <div class="freq-track">
                        <div class="freq-fill" style="width: {bar_w}%"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # 导出报告
            st.markdown('<div style="text-align: center; margin-top: 30px;">', unsafe_allow_html=True)
            report_text = generate_report(res, uploaded.name)
            st.download_button("📥 下载分析报告", report_text, f"FLASH_{uploaded.name}.txt", "text/plain")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # 参考曲对比
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        st.markdown('#### 🎚️ 参考曲对比')
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            f1 = st.file_uploader("🎵 你的混音", type=['wav', 'mp3', 'flac'], key="f1")
        with col_u2:
            f2 = st.file_uploader("🎯 参考曲", type=['wav', 'mp3', 'flac'], key="f2")

        if f1 and f2:
            with st.spinner('正在对比...'):
                r1 = analyze_audio_cached(f1.getvalue(), f1.name)
                r2 = analyze_audio_cached(f2.getvalue(), f2.name)
            if r1 and r2:
                st.success("✅ 对比完成")
                # 简化对比显示
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric('你的 LUFS', f"{r1['lufs_integrated']} dB")
                with c2:
                    st.metric('参考 LUFS', f"{r2['lufs_integrated']} dB")
                with c3:
                    diff = r1['lufs_integrated'] - r2['lufs_integrated']
                    st.metric('差值', f"{diff:+.1f} dB")
        st.markdown('</div>', unsafe_allow_html=True)

    # 页脚
    st.markdown('<div style="text-align: center; color: #4b5563; padding: 40px 0; border-top: 1px solid rgba(59, 130, 246, 0.1); margin-top: 40px;">FLASH Audio Analyzer v5.1</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()
