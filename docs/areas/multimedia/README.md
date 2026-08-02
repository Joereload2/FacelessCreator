# Multimedia

## Lectura obligatoria

[Arquitectura](../../ARCHITECTURE.md), [Dominio](../../DOMAIN.md), [Engineering](../../constitution/ENGINEERING.md), [Security](../../constitution/SECURITY.md) y [Testing](../../constitution/TESTING.md).

## Contrato actual

`FFmpegAdapter` encapsula disponibilidad, generación de fixtures, probe y render. No se construyen comandos desde UI. Los argumentos se pasan como lista sin shell.

El plan fija 1920×1080 y 30 fps en operación normal. Cada imagen se escala para cubrir y recorta al centro; el fixture ya cumple la resolución. El video usa H.264/yuv420p y audio AAC, con `faststart`. Preview y export usan el mismo render reproducible por ahora.

Los archivos se escriben con sufijo temporal, se validan con ffprobe y se renombran al destino final. SRT y manifiesto también se publican desde temporales o snapshots versionados.

## Fixtures

El adapter genera localmente tres PNG, dos alternativas y WAV de nueve segundos. No son assets productivos ni requieren red.

