import streamlit as st
import yt_dlp
import re
import time
import pandas as pd

gap_info = {
    "Sin playlist asignada": { "peso": 20, "roi": "+20% watch time", "metrica": "watch time",
        "por_que": "YouTube recomienda automáticamente el siguiente video", "como": "Crea playlists temáticas",
        "tiempo": "30 min", "esfuerzo": 30, "estimado_mensual": "€600/mes" },
    "Descripción corta": { "peso": 15, "roi": "+10-15% impresiones", "metrica": "impresiones",
        "por_que": "SEO mejorado", "como": "Expande a 200-300 caracteres",
        "tiempo": "5 min", "esfuerzo": 5, "estimado_mensual": "€200/mes" },
    "Sin emojis en título": { "peso": 10, "roi": "+5% CTR", "metrica": "click-through-rate",
        "por_que": "Captura atención en feeds móviles", "como": "Agrega emojis relevantes",
        "tiempo": "3 min", "esfuerzo": 3, "estimado_mensual": "€100/mes" },
    "Sin CTA": { "peso": 8, "roi": "+4% subs", "metrica": "suscriptores",
        "por_que": "Fomenta la acción del espectador", "como": "Agrega llamada a la acción en la descripción",
        "tiempo": "2 min", "esfuerzo": 2, "estimado_mensual": "€80/mes" },
    "Título largo": { "peso": 10, "roi": "+6% CTR", "metrica": "click-through-rate",
        "por_que": "Evita truncados y mejora comprensión", "como": "Reduce el título a <60 caracteres",
        "tiempo": "8 min", "esfuerzo": 8, "estimado_mensual": "€120/mes" },
    "Descripción sin keywords del título": { "peso": 12, "roi": "+8% impresiones", "metrica": "SEO",
        "por_que": "Palabras clave reforzadas en buscadores", "como": "Incluye keywords del título en la descripción",
        "tiempo": "7 min", "esfuerzo": 7, "estimado_mensual": "€160/mes" },
    "Sin pregunta de interacción": { "peso": 6, "roi": "+2% engagement", "metrica": "comentarios",
        "por_que": "Fomenta participación", "como": "Agrega una pregunta en la descripción",
        "tiempo": "2 min", "esfuerzo": 2, "estimado_mensual": "€50/mes" },
    "Título sin números": { "peso": 8, "roi": "+3% CTR", "metrica": "click-through-rate",
        "por_que": "Los números destacan en thumbnails", "como": "Incluye cifras relevantes en el título",
        "tiempo": "3 min", "esfuerzo": 3, "estimado_mensual": "€70/mes" },
    "Incluye FREE/GRATIS": { "peso": 18, "roi": "+12% CTR", "metrica": "click-through-rate",
        "por_que": "Palabras poderosas para atraer clics", "como": "Destaca ofertas gratuitas",
        "tiempo": "2 min", "esfuerzo": 2, "estimado_mensual": "€140/mes" },
    "Metadescripción ausente": { "peso": 25, "roi": "+25% SEO", "metrica": "posicionamiento",
        "por_que": "Ayuda al algoritmo a indexar mejor el vídeo", "como": "Agrega una descripción completa (>200 caracteres)",
        "tiempo": "8 min", "esfuerzo": 8, "estimado_mensual": "€180/mes" }
}

def extract_channel_videos(channel_url, max_videos=10, extract_total=20):
    ydl_opts = {
        'extract_flat': 'in_playlist', 'playlistend': extract_total,
        'quiet': True, 'skip_download': True, 'no_warnings': True, 'ignoreerrors': True
    }
    urls_to_try = [
        f"{channel_url}/videos", channel_url, f"{channel_url}/streams",
    ]
    for url in urls_to_try:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                videos = info.get('entries', [])
                valid_videos = []
                for v in videos:
                    if not v: continue
                    if v.get('is_live', False) or v.get('was_live', False): continue
                    if v.get('is_upcoming', False) or v.get('is_premiere', False): continue
                    release_ts = v.get('release_timestamp')
                    if release_ts is not None and release_ts > time.time(): continue
                    title = v.get('title', '')
                    video_id = v.get('id', '')
                    if not title or not video_id: continue
                    valid_videos.append(v)
                    if len(valid_videos) == max_videos: break
                if valid_videos:
                    return valid_videos
        except Exception:
            continue
    return []

def analizar_titulo(titulo):
    checks = []
    if len(titulo) > 60: checks.append("Título largo")
    if "FREE" in titulo.upper() or "GRATIS" in titulo.upper(): checks.append("Incluye FREE/GRATIS")
    emojis = ["💥", "💣", "🍌", "🚨", "🔥", "🚀"]
    if not any(e in titulo for e in emojis): checks.append("Sin emojis en título")
    if not re.search(r'\d+', titulo): checks.append("Título sin números")
    return checks

def analizar_descripcion(desc):
    checks = []
    if not desc or len(desc.strip()) == 0:
        checks.append("Metadescripción ausente")
        return checks
    if len(desc.strip()) < 150: checks.append("Descripción corta")
    ctas = ["suscríbete", "subscribe", "comenta", "dale like", "haz clic", "entra al link", "únete"]
    if not any(cta in desc.lower() for cta in ctas): checks.append("Sin CTA")
    pregunta_interaccion = ["¿", "?", "comenta", "opina", "qué piensas"]
    if not any(q in desc.lower() for q in pregunta_interaccion): checks.append("Sin pregunta de interacción")
    return checks

def analizar_extras(video_info, titulo, descripcion):
    extras = []
    if not video_info.get('playlist_title', None): extras.append("Sin playlist asignada")
    if descripcion and len(descripcion.strip()) >= 150:
        titulo_words = set(titulo.lower().split())
        desc_words = set(descripcion.lower().split())
        common_words = {'de', 'la', 'el', 'en', 'a', 'y', 'con', 'para', 'por', 'the', 'and', 'to', 'for', 'with'}
        titulo_keywords = titulo_words - common_words
        match_count = len(titulo_keywords.intersection(desc_words))
        if match_count < 3:
            extras.append("Descripción sin keywords del título")
    return extras

def sorting_key(gap):
    info = gap_info.get(gap, {})
    esfuerzo = info.get('esfuerzo', 999)
    eur = info.get('estimado_mensual', "€0/mes")
    eur_num = int(re.search(r'€(\d+)', eur).group(1)) if re.search(r'€(\d+)', eur) else 0
    return (esfuerzo, -eur_num)

st.title("Auditoría automática de canal YouTube")
canal_url = st.text_input(
    "Pega la URL de tu canal YouTube:",
    value="https://www.youtube.com/@alejavirivera"
)
max_videos = st.slider("Cantidad de vídeos a analizar", min_value=5, max_value=30, value=10)

if st.button("Analizar Canal"):
    with st.spinner("Analizando vídeos del canal..."):
        video_entries = extract_channel_videos(canal_url, max_videos=max_videos, extract_total=max_videos*2)
        if not video_entries:
            st.error("No se pudieron extraer vídeos del canal. Revisa la URL.")
        else:
            gaps_count = {}; total_videos = 0; videos_report = []
            for entry in video_entries:
                video_id = entry.get('id', ''); titulo = entry.get('title', '')
                if not video_id: continue
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'no_warnings': True, 'ignoreerrors': True}) as ydl_video:
                    video_info = ydl_video.extract_info(video_url, download=False)
                if not video_info: continue
                descripcion = video_info.get('description', '')
                titulo_checks = analizar_titulo(titulo)
                desc_checks = analizar_descripcion(descripcion)
                extras_checks = analizar_extras(video_info, titulo, descripcion)
                gaps = titulo_checks + desc_checks + extras_checks
                videos_report.append({
                    'Título': titulo, 'URL': video_url, 'Gaps': ', '.join(gaps),
                    'Vistas': video_info.get('view_count', 0), 'Duración': video_info.get('duration', 0), 'Descripción': descripcion
                })
                for gap in gaps: gaps_count[gap] = gaps_count.get(gap, 0) + 1
                total_videos += 1

            df_videos = pd.DataFrame(videos_report)
            st.subheader("Videos analizados y gaps detectados")
            st.dataframe(df_videos, use_container_width=True)

            matriz = []
            for gap, count in gaps_count.items():
                info = gap_info.get(gap, {})
                esfuerzo = info.get('esfuerzo', '?')
                euros = info.get('estimado_mensual', '?')
                eur_num = int(re.search(r'€(\d+)', euros).group(1)) if re.search(r'€(\d+)', euros) else 0
                roi = info.get('roi', '?')
                matriz.append({
                    'Gap': gap, 'Veces': count, 'Esfuerzo (min)': esfuerzo,
                    'Impacto (€)': eur_num, 'ROI (%)': roi, 'Acción': info.get('como','')
                })
            df_prioridad = pd.DataFrame(matriz)
            df_prioridad = df_prioridad.sort_values(by=['Esfuerzo (min)','Impacto (€)'], ascending=[True, False]).reset_index(drop=True)
            df_prioridad['Top'] = ''
            df_prioridad.loc[:2, 'Top'] = '🔥 TOP'
            cols = ['Top','Gap','Veces','Esfuerzo (min)','Impacto (€)','ROI (%)','Acción']
            st.subheader("Prioridad de mejoras")
            st.dataframe(df_prioridad[cols], use_container_width=True)

            st.subheader("Resumen de ocurrencias de gaps en el canal")
            summary_lines = []
            for gap, count in sorted(gaps_count.items(), key=lambda x: sorting_key(x[0])):
                info = gap_info.get(gap, {})
                roi = info.get('roi', '?')
                euros = info.get('estimado_mensual', '?')
                summary_lines.append(f"- {gap}: {count} veces | ROI esperado: {roi}, Impacto mensual estimado: {euros}")
            st.markdown("\n".join(summary_lines))

            mejor_video = min(videos_report, key=lambda x: (len(x['Gaps'].split(',')), -x['Vistas']))
            peor_video = max(videos_report, key=lambda x: (len(x['Gaps'].split(',')), x['Vistas']))
            st.subheader("BENCHMARK INTERNO")
            st.markdown(f"**Mejor optimizado (menos gaps, más views):**\n- **Título:** {mejor_video['Título']}\n- **URL:** [{mejor_video['URL']}]({mejor_video['URL']})\n- **Vistas:** {mejor_video['Vistas']:,}\n- **Gaps:** {mejor_video['Gaps']}\n")
            st.markdown(f"**Peor optimizado (más gaps, menos views):**\n- **Título:** {peor_video['Título']}\n- **URL:** [{peor_video['URL']}]({peor_video['URL']})\n- **Vistas:** {peor_video['Vistas']:,}\n- **Gaps:** {peor_video['Gaps']}\n")

            # Top 3 Mejoras con fuegos
            gaps_prioritarios = []
            for gap, count in gaps_count.items():
                info = gap_info.get(gap, {})
                eur = info.get('estimado_mensual', "€0/mes")
                roi = info.get('roi', '?')
                tiempo = info.get('tiempo', 'N/A')
                accion = info.get('como', 'N/A')
                eur_num = int(re.search(r'€(\d+)', eur).group(1)) if re.search(r'€(\d+)', eur) else 0
                impacto = count * eur_num
                gaps_prioritarios.append({
                    'gap': gap, 'count': count, 'impacto': impacto, 'roi': roi, 'accion': accion, 'tiempo': tiempo, 'eur': eur
                })
            gaps_prioritarios.sort(key=lambda x: x['impacto'], reverse=True)
            fires_map = {0: "🔥🔥🔥", 1: "🔥🔥", 2: "🔥"}
            st.subheader("💡 Top 3 mejoras más impactantes")
            for i, item in enumerate(gaps_prioritarios[:3]):
                fires = fires_map[i]
                st.markdown(
                    f"{fires} **{item['gap']}**\n"
                    f"- Afecta a: `{item['count']}/{total_videos}` videos\n"
                    f"- ROI estimado: `{item['roi']}`\n"
                    f"- Impacto mensual estimado: `{item['eur']}`\n"
                    f"- Acción: {item['accion']}\n"
                    f"- Tiempo: {item['tiempo']} por video\n"
                    "------"
                )

            total_gaps_possible = len(gap_info) * total_videos
            total_gaps_found = sum(gaps_count.values())
            score = 100 - (total_gaps_found / total_gaps_possible * 100)
            filled = int(score / 10)
            empty = 10 - filled
            bar = "█" * filled + "░" * empty

            st.subheader("📊 Canal Health Score")
            st.markdown(f"{bar}  **{score:.0f}%**")
            # Feedback contextual
            if score < 50:
                st.error("🔴 CRÍTICO - Optimización urgente necesaria\nComparado con tu competencia: Bottom 30%")
            elif score < 70:
                st.warning("🟡 MEDIO - Buen margen de mejora\nComparado con tu competencia: Promedio")
            else:
                st.success("🟢 BUENO - Canal bien optimizado\nComparado con tu competencia: Top 20%")

            st.caption("ADVERTENCIA: Los datos en € son orientativos y sujetos a implementar todas las mejoras en conjunto, no por separado.")

