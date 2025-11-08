import yt_dlp
import re

# ==================== CONFIGURACIÓN ====================
CHANNEL_URL = 'https://www.youtube.com/@SlimPotatohead'  # Cambiar por el canal que desees

# ==================== FUNCIONES DE EXTRACCIÓN CON FALLBACK ====================
def extract_channel_videos(channel_url, max_videos=5):
    """
    Extrae videos de un canal con sistema de fallback.
    Intenta primero la URL del canal, si falla, prueba con /videos
    """
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
        f"{channel_url}/streams",
    ]

    for attempt, url in enumerate(urls_to_try, 1):
        print(f"🔍 Intento {attempt}: {url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                videos = info.get('entries', [])

                # Filtrar videos válidos (excluir livestreams y pestañas)
                valid_videos = []
                for v in videos:
                    if not v:  # Saltar entradas None
                        continue

                    title = v.get('title', '')
                    video_id = v.get('id', '')

                    # Filtrar livestreams y pestañas
                    if not title or not video_id:
                        continue
                    if title.endswith(' - Videos') or title.endswith(' - Shorts'):
                        continue
                    if title.endswith(' - Live'):
                        continue
                    if v.get('is_live', False) or v.get('was_live', False):
                        continue

                    valid_videos.append(v)

                if valid_videos:
                    print(f"✅ Éxito! Encontrados {len(valid_videos)} videos válidos\n")
                    return valid_videos
                else:
                    print(f"⚠️  No se encontraron videos válidos (encontrados: {len(videos)})\n")

        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}\n")
            continue

    print("❌ No se pudieron extraer videos después de todos los intentos")
    return []

# ==================== FUNCIONES DE ANÁLISIS ====================
def analizar_titulo(titulo):
    checks = []
    if len(titulo) > 60:
        checks.append("Título largo")
    if "AI" in titulo.upper() or "IA" in titulo.upper():
        checks.append("Incluye IA")
    if "FREE" in titulo.upper() or "GRATIS" in titulo.upper():
        checks.append("Incluye FREE/GRATIS")
    emojis = ["💥", "💣", "🍌", "🚨", "🔥", "🚀"]
    if any(e in titulo for e in emojis):
        checks.append("Usa emoji")
    else:
        checks.append("Sin emojis en título")
    if not re.search(r'\d+', titulo):
        checks.append("Título sin números")
    return checks

def analizar_descripcion(desc):
    checks = []
    if not desc or len(desc.strip()) == 0:
        checks.append("Metadescripción ausente")
        return checks
    if len(desc.strip()) < 150:
        checks.append("Descripción corta")
    ctas = ["suscríbete", "subscribe", "comenta", "dale like", "haz clic", "entra al link", "únete"]
    if any(cta in desc.lower() for cta in ctas):
        checks.append("Incluye CTA")
    else:
        checks.append("Sin CTA")
    pregunta_interaccion = ["¿", "?", "comenta", "opina", "qué piensas"]
    if not any(q in desc.lower() for q in pregunta_interaccion):
        checks.append("Sin pregunta de interacción")
    return checks

def analizar_extras(video_info, titulo, descripcion):
    extras = []
    # Se considera asignada a playlist si existe playlist_title (nombre de la lista)
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

# ==================== INFORMACIÓN DE GAPS ====================
gap_info = {
    "Sin playlist asignada": {
        "peso": 20,
        "roi": "+15-25%",
        "metrica": "watch time",
        "por_que": "YouTube recomienda automáticamente el siguiente video",
        "como": "Crea playlists temáticas",
        "tiempo": "30 min",
        "prioridad": "🔥🔥🔥"
    },
    "Descripción corta": {
        "peso": 15,
        "roi": "+10-15%",
        "metrica": "impresiones",
        "por_que": "SEO mejorado",
        "como": "Expande a 200-300 caracteres",
        "tiempo": "3-4 min",
        "prioridad": "🔥🔥🔥"
    },
    "Título largo": {
        "peso": 10,
        "roi": "+5-10%",
        "metrica": "CTR",
        "por_que": "Títulos concisos son más atractivos",
        "como": "Acorta a menos de 60 caracteres",
        "tiempo": "2 min",
        "prioridad": "🔥🔥"
    },
    "Sin CTA": {
        "peso": 10,
        "roi": "+8-12%",
        "metrica": "engagement",
        "por_que": "Aumenta interacción y suscripciones",
        "como": "Añade 'suscríbete', 'comenta', etc.",
        "tiempo": "2 min",
        "prioridad": "🔥🔥"
    },
    "Sin pregunta de interacción": {
        "peso": 7,
        "roi": "+5-8%",
        "metrica": "comentarios",
        "por_que": "Aumenta engagement en comentarios",
        "como": "Añade pregunta al final de descripción",
        "tiempo": "1 min",
        "prioridad": "🔥"
    },
}

# ==================== SCRIPT PRINCIPAL ====================
print("=" * 60)
print(f"Analizando canal: {CHANNEL_URL}")
print("=" * 60)

# Extraer videos con fallback
video_entries = extract_channel_videos(CHANNEL_URL, max_videos=5)

if not video_entries:
    print("\n⚠️  No se pudieron extraer videos del canal.")
    print("Verifica que la URL sea correcta y que el canal tenga videos públicos.")
else:
    # Inicializa contadores y estructuras de reporte
    gaps_count = {}
    total_videos = 0
    videos_report = []
    videos_analizados = 0

    for entry in video_entries:
        video_id = entry.get('id', '')
        titulo = entry.get('title', '')

        if not video_id:
            print(f"⚠️  Saltando video sin ID: {titulo}")
            continue

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Extraer información completa del video
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'no_warnings': True, 'ignoreerrors': True}) as ydl_video:
            try:
                video_info = ydl_video.extract_info(video_url, download=False)
                if not video_info:
                    print(f"⚠️  Video no disponible: {titulo[:50]}...")
                    continue
                descripcion = video_info.get('description', '')
            except Exception as e:
                print(f"⚠️  Error obteniendo info de '{titulo[:50]}...': {str(e)[:50]}")
                continue

        # Si llegamos aquí, el video se analizó correctamente
        total_videos += 1
        videos_analizados += 1

        # Analizar gaps
        titulo_checks = analizar_titulo(titulo)
        desc_checks = analizar_descripcion(descripcion)
        extras_checks = analizar_extras(video_info, titulo, descripcion)

        # Junta todos los gaps
        gaps = titulo_checks + desc_checks + extras_checks

        # Reporte por vídeo
        videos_report.append({
            'title': titulo,
            'url': video_url,
            'gaps': gaps
        })

        # Acumula gaps por tipo
        for gap in gaps:
            gaps_count[gap] = gaps_count.get(gap, 0) + 1

    # ==================== REPORTE FINAL ====================
    if videos_analizados == 0:
        print("\n⚠️  No se pudieron analizar videos válidos del canal.")
    else:
        print(f"\n{'='*60}")
        print(f"Total de vídeos analizados: {total_videos}\n")
        print("Reporte de gaps detectados por vídeo:\n")

        for v in videos_report:
            print(f"- {v['title']}")
            print(f"  URL: {v['url']}")
            if v['gaps']:
                for g in v['gaps']:
                    info = gap_info.get(g, {})
                    extra = f" | {info['por_que']} // Acción: {info['como']}" if info else ""
                    print(f"    - {g}{extra}")
            else:
                print("    - (Sin gaps encontrados)")
            print()

        print(f"{'='*60}")
        print("Resumen de ocurrencias de gaps en el canal:\n")
        for gap, count in sorted(gaps_count.items(), key=lambda x: x[1], reverse=True):
            info = gap_info.get(gap, {})
            prioridad = info.get('prioridad', '')
            roi = info.get('roi', '')
            print(f"{prioridad} {gap}: {count}/{total_videos} veces {f'(ROI: {roi})' if roi else ''}")

        print(f"\n{'='*60}")
        print("💡 Top 3 mejoras más impactantes:")
        print(f"{'='*60}")

        # Ordenar gaps por frecuencia y peso
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
            print(f"\n{i}. {item['info'].get('prioridad', '')} {item['gap']}")
            print(f"   Afecta a: {item['count']}/{total_videos} videos")
            print(f"   ROI estimado: {item['info'].get('roi', 'N/A')}")
            print(f"   Acción: {item['info'].get('como', 'N/A')}")
            print(f"   Tiempo: {item['info'].get('tiempo', 'N/A')} por video")
