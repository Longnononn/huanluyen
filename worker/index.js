/**
 * Cloudflare Worker for AI System Automation
 * Handles: Config syncing, Telemetry logging, and GitHub Training Triggers.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const method = request.method;

    // --- 1. CORS Headers ---
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    };

    if (method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // --- 2. Xử lý yêu cầu POST (Update config / Trigger Training) ---
      if (method === "POST") {
        const body = await request.json();

        // A. Kích hoạt GitHub Action Train
        if (body.action === "trigger_training") {
          const repo = body.repo || "Longnononn/huanluyen";
          const ghResponse = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
              "Accept": "application/vnd.github.v3+json",
              "User-Agent": "Cloudflare-Worker-AI-System"
            },
            body: JSON.stringify({ event_type: "trigger-training" })
          });

          return new Response(JSON.stringify({ 
            success: ghResponse.status === 204, 
            status: ghResponse.status 
          }), { 
            status: ghResponse.status === 204 ? 200 : ghResponse.status,
            headers: { ...corsHeaders, "Content-Type": "application/json" } 
          });
        }

        // B. Cập nhật Telemetry / Logs (D1 Database)
        if (body.type === "telemetry" || body.type === "ERROR_LOG") {
          // Ghi vào D1 nếu có (giả lập lưu vào log)
          console.log("Telemetry received:", body);
          // await env.DB.prepare("INSERT INTO logs (data) VALUES (?)").bind(JSON.stringify(body)).run();
          return new Response(JSON.stringify({ success: true }), { 
            headers: { ...corsHeaders, "Content-Type": "application/json" } 
          });
        }

        // C. Cập nhật Cấu hình (Config)
        if (body.sensitivity || body.model_version) {
          // Ghi vào D1 hoặc KV
          // await env.CONFIG_KV.put("pc_config", JSON.stringify(body));
          console.log("Config updated:", body);
          return new Response(JSON.stringify({ success: true }), { 
            headers: { ...corsHeaders, "Content-Type": "application/json" } 
          });
        }
      }

      // --- 3. Xử lý yêu cầu GET (Lấy config hiện tại) ---
      // const config = await env.CONFIG_KV.get("pc_config", { type: "json" }) || {
      const defaultConfig = {
        "sensitivity": 0.35,
        "smoothness": 0.6,
        "recoil_compensation": 1.2,
        "target_class": 0,
        "auto_aim_key": "right_click",
        "model_version": "v1.0"
      };

      return new Response(JSON.stringify(defaultConfig), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }
  }
};
