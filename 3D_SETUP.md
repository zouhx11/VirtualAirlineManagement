# 3D Flight View Setup

## MapTiler API Key Setup

To use the 3D flight view, you need a MapTiler API key:

1. Go to [MapTiler Cloud](https://cloud.maptiler.com)
2. Sign up for a free account
3. Create a new API key from your dashboard
4. Replace the API key in `static/js/app.js`:

```javascript
this.maptilerApiKey = 'your_actual_api_key_here';
```

## Features

The 3D flight view includes:

- **Real-time 3D aircraft models** moving across a 3D terrain map
- **Flight tracking** with follow mode and free camera
- **Atmospheric effects** including sky, fog, and realistic lighting
- **Clickable flight list** to focus on specific aircraft
- **Seamless switching** between 2D map and 3D flight view

## Controls

- **3D Flight Mode**: Click the "3D Flight Mode" button on the map
- **Follow Mode**: Automatically follows the selected aircraft
- **Free Camera**: Manual camera control for exploration
- **Reset View**: Returns to default camera position
- **Flight Focus**: Click any flight in the sidebar to center on it

## Aircraft Models

Currently uses the Airbus A340 model from MapTiler's model library. Additional aircraft models can be added by:

1. Adding GLB files to the `static/models/` directory
2. Updating the `addMeshFromURL` calls in the JavaScript
3. Mapping aircraft types to specific models

## Performance

The 3D view is optimized for performance with:
- Efficient model reuse
- Smooth interpolation for movement
- Terrain rendering with low exaggeration
- Optimized lighting setup