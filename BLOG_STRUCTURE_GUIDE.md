# Guía de Estructura del Blog

## 📁 Estructura de Carpetas

```
blog/
├── guias/                    # Guías de uso y tutoriales
│   ├── guia-alertas-financieras.html
│   ├── guia-bull-agent.html
│   └── primeros-pasos-onboarding.html
│
├── releases/                 # Releases y actualizaciones
│   ├── release-v2-0-calendario-earnings.html
│   ├── release-v1-8-watchlists.html
│   └── release-v1-7-bull-agent-mejorado.html
│
├── noticias/                  # Noticias sobre IA y mercado
│   ├── chat-gpt-trading-futuro-bolsa.html
│   ├── ia-transformando-finanzas.html
│   └── prediccion-mercados-machine-learning.html
│
├── template-guia.html         # Template base para guías
├── template-release.html      # Template base para releases
├── template-noticia.html      # Template base para noticias
├── posts.json                 # Metadata de todos los posts
└── README.md                  # Documentación del blog
```

## 🎯 Cómo Funciona

### 1. Sistema de Templates

Cada tipo de contenido tiene su template base:
- **`template-guia.html`**: Para guías y tutoriales
- **`template-release.html`**: Para releases y actualizaciones
- **`template-noticia.html`**: Para noticias y artículos

### 2. Archivo `posts.json`

Este archivo contiene la metadata de todos los posts. El sistema de carga dinámica (`blog-loader.js`) lee este archivo y renderiza los posts automáticamente en `blog.html`.

### 3. Carga Dinámica

El archivo `js/blog-loader.js`:
- Carga `posts.json` al iniciar
- Genera las tarjetas de posts dinámicamente
- Las inserta en los carruseles correspondientes
- Reemplaza el contenido estático de `blog.html`

## 📝 Cómo Crear un Nuevo Post

### Paso 1: Crear el Archivo HTML

```bash
# Para una guía
cp blog/template-guia.html blog/guias/mi-nueva-guia.html

# Para un release
cp blog/template-release.html blog/releases/release-v2-1.html

# Para una noticia
cp blog/template-noticia.html blog/noticias/mi-noticia.html
```

### Paso 2: Editar el Contenido

Reemplaza las variables del template:
- `{{TITLE}}` → Título del post
- `{{DESCRIPTION}}` → Descripción breve
- `{{CONTENT}}` → Contenido HTML completo
- `{{IMAGE_URL}}` → URL de la imagen destacada
- Y todas las demás variables según el template

### Paso 3: Agregar a `posts.json`

Agrega la entrada en la sección correspondiente:

```json
{
  "slug": "mi-nueva-guia",
  "title": "Mi Nueva Guía",
  "description": "Descripción breve del contenido",
  "image_url": "https://images.unsplash.com/...",
  "publish_date": "25 de Diciembre, 2025",
  "read_time": 6,
  "author": "Equipo BullAnalytics",
  "keywords": "palabra1, palabra2, palabra3",
  "category": "Guía",
  "file": "guias/mi-nueva-guia.html"
}
```

### Paso 4: ¡Listo!

El post aparecerá automáticamente en `blog.html` cuando se cargue la página.

## 🔄 Flujo de Trabajo Recomendado

1. **Planificar**: Decide el tema y tipo de post
2. **Crear archivo**: Copia el template correspondiente
3. **Escribir contenido**: Edita el HTML con el contenido
4. **Agregar metadata**: Añade la entrada a `posts.json`
5. **Probar**: Verifica que se muestre correctamente en `blog.html`
6. **Publicar**: El post está listo para producción

## 📊 Ventajas de Esta Estructura

✅ **Organización clara**: Cada tipo de contenido en su carpeta
✅ **Fácil mantenimiento**: Un solo archivo JSON para metadata
✅ **Escalable**: Fácil agregar nuevos posts sin tocar `blog.html`
✅ **SEO optimizado**: Cada post tiene su propia URL y meta tags
✅ **Templates reutilizables**: Base consistente para todos los posts
✅ **Carga dinámica**: Los posts se cargan automáticamente

## 🎨 Personalización

### Colores de Badges

Los badges cambian de color según la categoría:
- **Guías**: Verde (`bg-green-100`)
- **Releases**: Azul (`bg-blue-100`)
- **Novedades**: Púrpura (`bg-purple-100`)
- **Mejoras**: Verde (`bg-green-100`)
- **Videos**: Rojo (`bg-red-100`)
- **Artículos**: Índigo (`bg-indigo-100`)
- **Noticias**: Teal (`bg-teal-100`)

### Estilos de Contenido

El contenido usa la clase `prose` de Tailwind para estilos tipográficos automáticos. Puedes usar:
- `<h2>`, `<h3>` para títulos
- `<p>` para párrafos
- `<ul>`, `<ol>` para listas
- `<code>` para código
- `<a>` para enlaces

## 📱 Responsive

Todos los templates están optimizados para:
- Desktop (pantallas grandes)
- Tablet (pantallas medianas)
- Mobile (pantallas pequeñas)

## 🔍 SEO

Cada post incluye:
- Meta tags completos
- Open Graph tags para redes sociales
- Twitter Card tags
- URL canónica
- Estructura semántica HTML

## 🚀 Próximos Pasos

1. Crear más posts usando los templates
2. Agregar imágenes personalizadas para cada post
3. Optimizar contenido para SEO
4. Agregar comentarios (opcional)
5. Implementar búsqueda de posts (opcional)

