# Estructura del Blog de BullAnalytics

## Organización

El blog está organizado en carpetas por temática:

```
blog/
├── guias/              # Guías de uso y tutoriales
├── releases/           # Releases y actualizaciones
├── noticias/           # Noticias sobre IA y mercado bursátil
├── template-guia.html  # Template base para guías
├── template-release.html # Template base para releases
├── template-noticia.html # Template base para noticias
└── posts.json          # Archivo JSON con metadata de todos los posts
```

## Cómo Crear un Nuevo Post

### 1. Para una Guía

1. **Copia el template:**
   ```bash
   cp blog/template-guia.html blog/guias/mi-nueva-guia.html
   ```

2. **Edita el archivo HTML:**
   - Reemplaza `{{TITLE}}` con el título del post
   - Reemplaza `{{DESCRIPTION}}` con la descripción
   - Reemplaza `{{CONTENT}}` con el contenido HTML del artículo
   - Actualiza las meta tags (Open Graph, Twitter)
   - Actualiza la imagen destacada

3. **Agrega el post a `posts.json`:**
   ```json
   {
     "slug": "mi-nueva-guia",
     "title": "Mi Nueva Guía",
     "description": "Descripción breve",
     "image_url": "https://...",
     "publish_date": "Fecha de publicación",
     "read_time": 5,
     "author": "Autor",
     "keywords": "palabras, clave",
     "category": "Guía",
     "file": "guias/mi-nueva-guia.html"
   }
   ```

### 2. Para un Release

1. **Copia el template:**
   ```bash
   cp blog/template-release.html blog/releases/release-v2-1.html
   ```

2. **Edita el archivo:**
   - Similar a las guías, pero incluye secciones especiales:
     - `{{FEATURES_LIST}}`: Lista de nuevas funcionalidades
     - `{{CHANGELOG}}`: Lista de cambios
     - `{{VERSION}}`: Versión del release

3. **Agrega a `posts.json`** en la sección `releases`

### 3. Para una Noticia

1. **Copia el template:**
   ```bash
   cp blog/template-noticia.html blog/noticias/mi-noticia.html
   ```

2. **Edita el archivo:**
   - Similar a las guías
   - Puede incluir `{{TAGS_SECTION}}` para tags relacionados

3. **Agrega a `posts.json`** en la sección `noticias`

## Variables del Template

### Variables Comunes (todos los templates):
- `{{TITLE}}`: Título del artículo
- `{{DESCRIPTION}}`: Descripción breve
- `{{IMAGE_URL}}`: URL de la imagen destacada
- `{{SLUG}}`: Slug del post (para URLs)
- `{{PUBLISH_DATE}}`: Fecha de publicación
- `{{READ_TIME}}`: Tiempo estimado de lectura
- `{{AUTHOR}}`: Autor del artículo
- `{{KEYWORDS}}`: Palabras clave para SEO
- `{{CONTENT}}`: Contenido HTML del artículo
- `{{CANONICAL_URL}}`: URL canónica del post
- `{{RELATED_ARTICLES}}`: HTML de artículos relacionados

### Variables Específicas de Releases:
- `{{VERSION}}`: Versión del release (ej: v2.0.0)
- `{{FEATURES_LIST}}`: Lista HTML de nuevas funcionalidades
- `{{CHANGELOG}}`: Lista HTML de cambios

### Variables Específicas de Noticias:
- `{{CATEGORY_BADGE}}`: Badge HTML de categoría
- `{{TAGS_SECTION}}`: Sección HTML de tags

## Sistema de Carga Dinámica

El archivo `js/blog-loader.js` carga automáticamente los posts desde `posts.json` y los renderiza en `blog.html`. 

**No necesitas modificar `blog.html` manualmente** - solo agrega nuevos posts a `posts.json` y crea los archivos HTML correspondientes.

## Ejemplo Completo

### 1. Crear el archivo HTML:
```bash
cp blog/template-guia.html blog/guias/guia-watchlists.html
```

### 2. Editar el contenido en `guia-watchlists.html`

### 3. Agregar a `posts.json`:
```json
{
  "slug": "guia-watchlists",
  "title": "Cómo Usar Watchlists en BullAnalytics",
  "description": "Aprende a crear y gestionar tus listas personalizadas de activos.",
  "image_url": "https://images.unsplash.com/photo-...",
  "publish_date": "20 de Diciembre, 2025",
  "read_time": 6,
  "author": "Equipo BullAnalytics",
  "keywords": "watchlists, listas, seguimiento, activos",
  "category": "Guía",
  "file": "guias/guia-watchlists.html"
}
```

### 4. El post aparecerá automáticamente en blog.html

## Buenas Prácticas

1. **Slugs únicos**: Usa slugs descriptivos y únicos (ej: `guia-alertas-financieras`)
2. **Imágenes**: Usa imágenes de alta calidad (mínimo 800px de ancho)
3. **SEO**: Completa todas las meta tags para mejor SEO
4. **Contenido**: Usa HTML semántico en el contenido
5. **Enlaces**: Usa rutas relativas para enlaces internos (ej: `../../dashboard.html`)
6. **Fechas**: Usa formato legible (ej: "15 de Diciembre, 2025")

## Estructura de Contenido HTML

El contenido debe usar clases de Tailwind y estructura semántica:

```html
<div class="prose prose-lg dark:prose-invert max-w-none">
    <h2>Título de Sección</h2>
    <p>Párrafo de texto...</p>
    
    <h3>Subtítulo</h3>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    
    <p>Más contenido...</p>
</div>
```

## Mantenimiento

- **Orden de posts**: Los posts se muestran en el orden que aparecen en `posts.json`
- **Posts antiguos**: Puedes mover posts antiguos a una carpeta `archivo/` si lo deseas
- **Actualizaciones**: Para actualizar un post, simplemente edita su archivo HTML

