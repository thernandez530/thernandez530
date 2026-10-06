# Perfil animado de Tomás

Los SVG están versionados en este repositorio y no dependen de servicios de estadísticas externos. El texto del README permanece legible si las animaciones están deshabilitadas.

## Actualizar

Edita `README.md` para cambiar el texto y `scripts/generate.py` para cambiar la tarjeta. Ejecuta:

```sh
python scripts/generate.py
```

El workflow `Update animated profile` actualiza las contribuciones cada día a las 10:17 UTC y se puede ejecutar desde Actions → Run workflow. Usa el token incorporado de GitHub Actions, sin secretos personales adicionales. Los horarios programados pueden sufrir retrasos de GitHub.

Si Actions está deshabilitado, habilítalo en el repositorio. Si una política bloquea la escritura del token, permite escritura de contenidos para este workflow. Un error al consultar GitHub conserva el calendario anterior y hace fallar la ejecución en lugar de publicar datos inventados.

## Archivos

- `assets/info-card.svg`: tarjeta animada con presentación y stack.
- `assets/contributions.svg`: calendario generado a partir de datos reales.
- `data/contributions.json`: se crea en la primera ejecución correcta del workflow.
- `scripts/generate.py`: generador Python 3.11+, sin dependencias externas.
- `.github/workflows/update-profile-art.yml`: actualización diaria.

El calendario ocupa todo el ancho; debajo se muestran el retrato y las estadísticas en dos columnas, siguiendo la referencia. Las animaciones se reproducen una vez; hay soporte de movimiento reducido y títulos accesibles. El retrato ASCII se genera desde la ilustración elegida, guardada en `assets/portrait-source.jpg`. El generador aísla la cabeza, conserva las proporciones y produce un SVG animado. Para regenerarlo localmente, instala Pillow y ejecuta `python scripts/make_portrait.py`. El argumento `--source-file RUTA` admite otra copia de la misma ilustración. La actualización diaria usa este archivo y no descarga el avatar de GitHub. Las estadísticas se derivan del mismo calendario real.

Inspiración: [guía de Avi Vashishta](https://www.avivashishta.com/blog/build-animated-github-profile-readme). Implementación adaptada para Tomás, con consulta GraphQL mediante el token incorporado de Actions.
