import psycopg2
import json
import os

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("Set GOOGLE_MAPS_API_KEY before running generate_map.py")

DB_CONFIG = {
    "dbname": "land_registry",
    "user": "postgres",
    "password": "mahek",  # <-- Put your pgAdmin password
    "host": "localhost",
    "port": "5433"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

query = """
    SELECT 
        survey_gat_no,
        khata_no,
        total_area_ha,
        cultivable_area_ha,
        owner_names,
        ROUND((ST_Area(geom::geography) / 10000.0)::numeric, 4) AS gis_area_ha,
        ROUND(ST_Perimeter(geom::geography)::numeric, 2) AS perimeter_m,
        ST_AsGeoJSON(geom) AS geojson
    FROM cadastral_parcels
    WHERE geom IS NOT NULL;
"""

cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

features = []
for row in rows:
    survey_gat, khata, total_area, cultivable, owner, gis_area, perimeter, geom_json = row
    if not geom_json:
        continue
    
    features.append({
        "type": "Feature",
        "geometry": json.loads(geom_json),
        "properties": {
            "survey_gat_no": survey_gat,
            "khata_no": khata,
            "total_area_ha": float(total_area),
            "cultivable_area_ha": float(cultivable) if cultivable else 0.0,
            "gis_area_ha": float(gis_area) if gis_area else 0.0,
            "perimeter_m": float(perimeter) if perimeter else 0.0,
            "owner_names": owner
        }
    })

geojson_data = {"type": "FeatureCollection", "features": features}

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Kadav Cadastral Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        #map {{ height: 100vh; width: 100vw; }}
        .info-panel {{
            position: absolute; top: 15px; right: 15px; z-index: 1000;
            background: rgba(255, 255, 255, 0.95); padding: 14px 18px; border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.25); max-width: 300px;
        }}
        .info-panel h3 {{ margin: 0 0 6px; font-size: 15px; color: #2c3e50; }}
        .info-panel p {{ margin: 3px 0; font-size: 13px; color: #555; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>Kadav Village Land Registry</h3>
        <p><strong>Mapped Parcels:</strong> {len(features)}</p>
        <p style="font-size: 11px; color: #7f8c8d;">Click any green plot to view survey details.</p>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
    <script src="https://unpkg.com/leaflet.gridlayer.googlemutant@0.15.0/dist/Leaflet.GoogleMutant.js"></script>
    <script>
        const googleSatellite = L.gridLayer.googleMutant({{
            type: 'satellite',
            maxZoom: 20
        }});

        const map = L.map('map', {{
            center: [18.9163, 73.3255],
            zoom: 16,
            layers: [googleSatellite]
        }});

        L.control.layers({{ "Google Satellite": googleSatellite }}).addTo(map);

        const geojsonData = {json.dumps(geojson_data)};

        function onEachFeature(feature, layer) {{
            const p = feature.properties;
            const popupContent = `
                <div style="font-size: 13px; line-height: 1.4;">
                    <b style="font-size: 15px; color: #16a085;">Gat No: ${{p.survey_gat_no}}</b><br/>
                    <b>Total Area:</b> ${{p.total_area_ha}} ha<br/>
                    <b>GIS Area:</b> ${{p.gis_area_ha}} ha<br/>
                    <b>Perimeter:</b> ${{p.perimeter_m}} m<br/>
                    <b>Cultivable Area:</b> ${{p.cultivable_area_ha}} ha<br/>
                    <hr style="margin: 6px 0; border: 0; border-top: 1px solid #ccc;"/>
                    <b>Label:</b> ${{p.owner_names}}
                </div>
            `;
            layer.bindPopup(popupContent);
            
            layer.on('mouseover', function () {{
                this.setStyle({{ weight: 3, color: '#f1c40f', fillOpacity: 0.7 }});
            }});
            layer.on('mouseout', function () {{
                geojsonLayer.resetStyle(this);
            }});
        }}

        const geojsonLayer = L.geoJSON(geojsonData, {{
            style: function() {{
                return {{
                    color: '#27ae60',
                    weight: 2,
                    opacity: 1,
                    fillColor: '#2ecc71',
                    fillOpacity: 0.4
                }};
            }},
            onEachFeature: onEachFeature
        }}).addTo(map);

        if (geojsonData.features.length > 0) {{
            map.fitBounds(geojsonLayer.getBounds(), {{ padding: [40, 40] }});
        }}
    </script>
</body>
</html>
"""

with open("cadastral_map.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Generated cadastral_map.html cleanly.")