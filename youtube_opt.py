import os
os.environ['STREAMLIT_ENABLE_PYARROW'] = 'false'

# app.py
import streamlit as st
import yt_dlp
import re

# ==================== CONFIGURACIÓN ====================
st.set_page_config(
    page_title="YouTube Gap Analyzer",
    page_icon="📊",
    layout="centered"
)

# ==================== CSS PERSONALIZADO ====================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF0000;
        font-weight: bold;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES DE ANÁLISIS ====================

def extract_channel_videos(channel_url, max_videos=5):
    """Extrae videos del canal con fallback"""
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'playlistend': max_videos,
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'ignoreerrors': True
    }

    urls_to_try = [
        f"{channel_url}/videos",
        channel_url,
    ]

    for url in urls_to_try:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                videos = info.get('entries', [])

                valid_videos = []
                for v in videos:
                    if not v:
                        continue
                    title = v.get('title', '')
                    video_id = v.get('id', '')

                    if not title or not video_id:
                        continue
                    if title.endswith((' - Videos', ' - Shorts', ' - Live')):
                        continue
                    if v.get('is_live', False) or v.get('was_live', False):
                        continue

                    valid_videos.append(v)

                if valid_videos:
                    return valid_videos
        except Exception as e:
            continue

    return []

def analizar_titulo(titulo):
    """Analiza gaps en el título"""
    checks = []
    if len(titulo) > 60:
        checks.append("Título largo")
    if "AI" in titulo.upper() or "IA" in titulo.upper():
        checks.append("Incluye IA")
    if "FREE" in titulo.upper() or "GRATIS" in titulo.upper():
        checks.append("Incluye FREE/GRATIS")
    emojis = ["💥", "💣", "🍌", "🚨", "🔥", "🚀"]
    if not any(e in titulo for e in emojis):
        checks.append("Sin emojis en título")
    if not re.search(r'\d+', titulo):
        checks.append("Título sin números")
    return checks

def analizar_descripcion(desc):
    """Analiza gaps en la descripción"""
    checks = []
    if not desc or len(desc.strip()) == 0:
        checks.append("Metadescripción ausente")
        return checks
    if len(desc.strip()) < 150:
        checks.append("Descripción corta")

    ctas = ["suscríbete", "subscribe", "comenta", "dale like", "haz clic", "entra al link", "únete"]
    if not any(cta in desc.lower() for cta in ctas):
        checks.append("Sin CTA")

    if desc.count('#') == 0:
        checks.append("Sin hashtags en descripción")

    pregunta_interaccion = ["¿", "?", "comenta", "opina", "qué piensas"]
    if not any(q in desc.lower() for q in pregunta_interaccion):
        checks.append("Sin pregunta de interacción")

    return checks

def analizar_extras(video_info, titulo, descripcion):
    """Analiza gaps adicionales"""
    extras = []

    if not video_info.get('playlist_title', None):
        extras.append("Sin playlist asignada")

    if descripcion and len(descripcion.strip()) >= 150:
        titulo_words = set(titulo.lower().split())
        desc_words = set(descripcion.lower().split())
        common_words = {'de', 'la', 'el', 'en', 'a', 'y', 'con', 'para', 'por', 'the', 'and', 'to', 'for', 'with'}
        titulo_keywords = titulo_words - common_words
        match_count = len(titulo_keywords.intersection(desc_words))
        if match_count < 3:
            extras.append("Descripción sin keywords del título")

    return extras

# Información de gaps con ROI
gap_info = {
    "Sin playlist asignada": {"peso": 20, "roi": "+15-25%", "prioridad": "🔥🔥🔥", "accion": "Crea playlists temáticas"},
    "Descripción corta": {"peso": 15, "roi": "+10-15%", "prioridad": "🔥🔥🔥", "accion": "Expande a 200-300 caracteres"},
    "Título largo": {"peso": 10, "roi": "+5-10%", "prioridad": "🔥🔥", "accion": "Acorta a < 60 caracteres"},
    "Sin CTA": {"peso": 10, "roi": "+8-12%", "prioridad": "🔥🔥", "accion": "Añade 'suscríbete', 'comenta', etc."},
    "Sin hashtags en descripción": {"peso": 5, "roi": "+3-5%", "prioridad": "🔥", "accion": "Añade 2-3 hashtags relevantes"},
    "Sin pregunta de interacción": {"peso": 7, "roi": "+5-8%", "prioridad": "🔥", "accion": "Añade pregunta al final"},
    "Descripción sin keywords del título": {"peso": 8, "roi": "+5-10%", "prioridad": "🔥🔥", "accion": "Incluye palabras clave del título"},
}

def analizar_canal(channel_url, num_videos=5):
    """
    Función principal que analiza el canal
    Retorna un string formateado con los resultados
    """
    resultado = []
    resultado.append("=" * 60)
    resultado.append(f"ANÁLISIS DE CANAL: {channel_url}")
    resultado.append("=" * 60)
    resultado.append("")

    # Extraer videos
    resultado.append(f"🔍 Extrayendo últimos {num_videos} videos...")
    videos = extract_channel_videos(channel_url, max_videos=num_videos)

    if not videos:
        resultado.append("❌ No se pudieron extraer videos del canal.")
        resultado.append("Verifica que la URL sea correcta.")
        return "\n".join(resultado)

    resultado.append(f"✅ Encontrados {len(videos)} videos\n")
    resultado.append("")

    # Analizar cada video
    gaps_count = {}
    videos_report = []
    total_videos = 0

    for entry in videos:
        video_id = entry.get('id', '')
        titulo = entry.get('title', '')

        if not video_id:
            continue

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'ignoreerrors': True}) as ydl_video:
                video_info = ydl_video.extract_info(video_url, download=False)
                if not video_info:
                    continue
                descripcion = video_info.get('description', '')
        except:
            continue

        total_videos += 1

        # Analizar gaps
        titulo_checks = analizar_titulo(titulo)
        desc_checks = analizar_descripcion(descripcion)
        extras_checks = analizar_extras(video_info, titulo, descripcion)

        gaps = titulo_checks + desc_checks + extras_checks

        videos_report.append({
            'title': titulo,
            'url': video_url,
            'gaps': gaps
        })

        for gap in gaps:
            gaps_count[gap] = gaps_count.get(gap, 0) + 1

    # Generar reporte
    if total_videos == 0:
        resultado.append("⚠️ No se pudieron analizar videos válidos.")
        return "\n".join(resultado)

    # Resumen por video
    resultado.append("📊 REPORTE POR VIDEO:")
    resultado.append("-" * 60)
    for v in videos_report:
        resultado.append(f"\n📹 {v['title']}")
        resultado.append(f"   {v['url']}")
        if v['gaps']:
            for g in v['gaps']:
                info = gap_info.get(g, {})
                prioridad = info.get('prioridad', '')
                accion = info.get('accion', '')
                resultado.append(f"   {prioridad} {g}")
                if accion:
                    resultado.append(f"      → {accion}")
        else:
            resultado.append("   ✅ Sin gaps detectados")

    # Resumen general
    resultado.append("\n")
    resultado.append("=" * 60)
    resultado.append("📈 RESUMEN DE GAPS:")
    resultado.append("=" * 60)

    for gap, count in sorted(gaps_count.items(), key=lambda x: x[1], reverse=True):
        info = gap_info.get(gap, {})
        prioridad = info.get('prioridad', '')
        roi = info.get('roi', '')
        porcentaje = (count / total_videos) * 100
        resultado.append(f"{prioridad} {gap}: {count}/{total_videos} videos ({porcentaje:.0f}%)")
        if roi:
            resultado.append(f"   ROI estimado: {roi}")

    # Top 3 prioridades
    resultado.append("\n")
    resultado.append("=" * 60)
    resultado.append("🎯 TOP 3 MEJORAS MÁS IMPACTANTES:")
    resultado.append("=" * 60)

    gaps_prioritarios = []
    for gap, count in gaps_count.items():
        info = gap_info.get(gap, {})
        peso = info.get('peso', 0)
        if peso > 0:
            impacto = count * peso
            gaps_prioritarios.append({
                'gap': gap,
                'count': count,
                'info': info,
                'impacto': impacto
            })

    gaps_prioritarios.sort(key=lambda x: x['impacto'], reverse=True)

    for i, item in enumerate(gaps_prioritarios[:3], 1):
        resultado.append(f"\n{i}. {item['info'].get('prioridad', '')} {item['gap']}")
        resultado.append(f"   Afecta a: {item['count']}/{total_videos} videos")
        resultado.append(f"   ROI: {item['info'].get('roi', 'N/A')}")
        resultado.append(f"   ✅ Acción: {item['info'].get('accion', 'N/A')}")

    # Score final
    total_gaps = sum(gaps_count.values())
    avg_gaps = total_gaps / total_videos if total_videos > 0 else 0
    score = max(0, 100 - (avg_gaps * 7))  # Ajustado para ser más generoso

    resultado.append("\n")
    resultado.append("=" * 60)
    resultado.append(f"📊 SCORE DEL CANAL: {int(score)}%")
    resultado.append("=" * 60)

    if score >= 80:
        resultado.append("🎉 ¡Excelente! Tu canal está muy optimizado.")
    elif score >= 60:
        resultado.append("👍 Bien! Algunas mejoras pueden llevar tu canal al siguiente nivel.")
    else:
        resultado.append("💪 Hay mucho potencial de mejora. ¡Empieza por el Top 3!")

    return "\n".join(resultado)

# ==================== INTERFAZ STREAMLIT ====================

st.markdown('<h1 class="main-header">📊 Análisis rápido de Canal YouTube</h1>', unsafe_allow_html=True)

st.markdown("""
### 🚀 Descubre qué le falta a tus videos para crecer más rápido

Analiza tu canal en segundos y obtén recomendaciones accionables para:
- ✅ Aumentar el CTR (Click-Through Rate)
- ✅ Mejorar el engagement
- ✅ Optimizar para el algoritmo de YouTube
""")

st.markdown("---")

url = st.text_input(
    "Ingresa la URL de tu canal de YouTube:",
    placeholder="https://www.youtube.com/@tucanal",
    help="Ejemplo: https://www.youtube.com/@MrBeast"
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Analizar últimos 5 vídeos", type="primary", use_container_width=True):
        if url and 'youtube.com/@' in url:
            with st.spinner('⚡ Analizando los últimos 5 vídeos... (30 seg)'):
                resultado = analizar_canal(url, num_videos=5)
                st.text_area("📊 Resultado del Análisis", resultado, height=600)

                # Botón de descarga
                st.download_button(
                    label="📥 Descargar reporte",
                    data=resultado,
                    file_name=f"analisis_youtube_{url.split('@')[-1]}.txt",
                    mime="text/plain"
                )
        else:
            st.error("⚠️ Por favor, ingresa una URL válida de YouTube")

with col2:
    if st.button("🚀 Análisis completo - 20 vídeos", use_container_width=True):
        st.info("""
        ### 🔒 Próximamente - Análisis Premium

        El análisis de 20 videos incluirá:
        - 📊 Estadísticas avanzadas
        - 🎯 Comparación con competidores
        - 💡 Recomendaciones con IA
        - 📄 Reporte PDF descargable

        💰 **Precio:** $9.99

        [📧 Únete a la lista de espera](mailto:tu@email.com?subject=Lista%20Premium)
        """)

# Footer con información adicional
st.markdown("---")
st.markdown("""
<div style='text-
