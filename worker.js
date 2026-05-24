async function fetchAndSaveTraffic(env, days = 1) {
  try {
    const api_url = `https://api.ibb.gov.tr/tkmservices/api/TrafficData/v1/TrafficIndexHistory/${days}/5M`;
    const response = await fetch(api_url);
    if (!response.ok) return { success: false, error: `IBB API Error: ${response.status}` };
    
    const data = await response.json();
    if (!data || !Array.isArray(data)) return { success: false, error: "Invalid data from IBB API" };

    const statements = data.map(item => {
      let date_str = item.TrafficIndexDate;
      if (date_str) date_str = String(date_str).slice(0, 19);
      return env.DB.prepare("INSERT OR IGNORE INTO traffic_index (traffic_index, traffic_index_date) VALUES (?, ?)")
        .bind(item.TrafficIndex, date_str);
    });

    // Execute in batches
    const batchSize = 100;
    for (let i = 0; i < statements.length; i += batchSize) {
      const batch = statements.slice(i, i + batchSize);
      await env.DB.batch(batch);
    }

    return { success: true, count: data.length, date: new Date().toISOString() };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    // /api/update endpoint (Manual or Force update)
    if (url.pathname === '/api/update') {
      const days = url.searchParams.get('days') || 1;
      const result = await fetchAndSaveTraffic(env, days);
      return new Response(JSON.stringify(result), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    // /api/traffic endpoint
    if (url.pathname === '/api/traffic') {
      try {
        if (!env.DB) {
          return new Response(JSON.stringify({ error: "D1 Database binding 'DB' is missing." }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
          });
        }

        // Auto-create table if it doesn't exist
        await env.DB.prepare(`
          CREATE TABLE IF NOT EXISTS traffic_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traffic_index INTEGER,
            traffic_index_date TEXT UNIQUE
          )
        `).run();

        const start = url.searchParams.get('start');
        const end = url.searchParams.get('end');

        let query = "SELECT traffic_index, traffic_index_date FROM traffic_index";
        let params = [];

        if (start && end) {
          query += " WHERE traffic_index_date BETWEEN ? AND ?";
          params = [start, end];
        } else if (start) {
          query += " WHERE traffic_index_date >= ?";
          params = [start];
        }

        query += " ORDER BY traffic_index_date ASC";

        let stmt = env.DB.prepare(query);
        if (params.length > 0) {
          stmt = stmt.bind(...params);
        }

        const { results } = await stmt.all();

        return new Response(JSON.stringify(results), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
      }
    }

    // /api/latest-dates endpoint
    if (url.pathname === '/api/latest-dates') {
      try {
        if (!env.DB) {
          return new Response(JSON.stringify({ error: "D1 Database binding 'DB' is missing." }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
          });
        }
        
        const { results } = await env.DB.prepare("SELECT MAX(traffic_index_date) as max_date FROM traffic_index").all();
        const max_date = results.length > 0 ? results[0].max_date : null;

        return new Response(JSON.stringify({ traffic_index: max_date }), {
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
      }
    }

    // /api/export-csv endpoint
    if (url.pathname === '/api/export-csv') {
      try {
        const start = url.searchParams.get('start');
        const end = url.searchParams.get('end');

        let query = "SELECT traffic_index, traffic_index_date FROM traffic_index";
        let params = [];
        if (start && end) {
          query += " WHERE traffic_index_date BETWEEN ? AND ?";
          params = [start, end];
        } else if (start) {
          query += " WHERE traffic_index_date >= ?";
          params = [start];
        }
        query += " ORDER BY traffic_index_date ASC";

        const { results } = await env.DB.prepare(query).bind(...params).all();

        // Generate CSV with BOM for Excel
        let csv = "\ufeffsep=;\n";
        csv += "Tarih;Trafik İndeksi\n";
        results.forEach(row => {
          let d = row.traffic_index_date ? String(row.traffic_index_date).replace('T', ' ') : '';
          csv += `${d};${row.traffic_index}\n`;
        });

        const fileName = `ibb_trafik_verisi_${new Date().toISOString().slice(0, 10)}.csv`;

        return new Response(csv, {
          headers: {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': `attachment; filename="${fileName}"`,
            'Access-Control-Allow-Origin': '*'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
      }
    }

    // Serve static assets for all other requests
    return env.ASSETS.fetch(request);
  },

  async scheduled(event, env, ctx) {
    // Automated hourly update
    ctx.waitUntil(fetchAndSaveTraffic(env, 1));
  }
};
