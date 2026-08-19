// apify-ingest
// Recebe o webhook do Apify, busca os itens do dataset e entrega ao Postgres.
// A logica de derivacao e roteamento vive em SQL (ingest_apify_items),
// para os pesos do classificador poderem ser ajustados sem novo deploy.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const APIFY_TOKEN = Deno.env.get("APIFY_TOKEN")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ erro: "use POST" }, 405);

  const db = createClient(SUPABASE_URL, SERVICE_KEY);

  let payload: any;
  try {
    payload = await req.json();
  } catch {
    return json({ erro: "corpo nao e JSON valido" }, 400);
  }

  const evento: string = payload?.eventType ?? "desconhecido";
  const recurso = payload?.resource ?? payload?.eventData ?? {};
  const runId: string = recurso?.id ?? payload?.eventData?.actorRunId ?? `sem_id_${Date.now()}`;
  const datasetId: string | undefined = recurso?.defaultDatasetId;

  // Teste do botao "Save & test" do Apify manda payload sem dataset real.
  if (evento.includes("TEST") || !datasetId) {
    await db.from("apify_runs").upsert({
      run_id: runId,
      dataset_id: datasetId ?? null,
      status: "teste_ou_sem_dataset",
      erro: `evento=${evento} sem defaultDatasetId`,
    });
    return json({ ok: true, nota: "webhook recebido, sem dataset para processar", evento });
  }

  // Rodada que falhou: registra e sai.
  if (evento.includes("FAILED") || evento.includes("ABORTED") || evento.includes("TIMED_OUT")) {
    await db.from("apify_runs").upsert({
      run_id: runId,
      dataset_id: datasetId,
      actor_id: recurso?.actId ?? null,
      status: "falhou",
      erro: evento,
    });
    return json({ ok: true, nota: "rodada falhou, registrada", evento });
  }

  // Nao reprocessa dataset ja processado.
  const { data: jaFeito } = await db
    .from("apify_runs")
    .select("run_id, status")
    .eq("run_id", runId)
    .maybeSingle();

  if (jaFeito?.status === "processado") {
    return json({ ok: true, nota: "rodada ja processada", run_id: runId });
  }

  // Busca os itens do dataset, paginado.
  const itens: unknown[] = [];
  const limite = 500;
  let offset = 0;

  try {
    while (true) {
      const url =
        `https://api.apify.com/v2/datasets/${datasetId}/items` +
        `?clean=true&format=json&limit=${limite}&offset=${offset}`;
      const r = await fetch(url, {
        headers: { Authorization: `Bearer ${APIFY_TOKEN}` },
      });
      if (!r.ok) throw new Error(`Apify ${r.status}: ${await r.text()}`);
      const lote = await r.json();
      if (!Array.isArray(lote) || lote.length === 0) break;
      itens.push(...lote);
      if (lote.length < limite) break;
      offset += limite;
      if (offset > 20000) break; // guarda-corpo
    }
  } catch (e) {
    await db.from("apify_runs").upsert({
      run_id: runId,
      dataset_id: datasetId,
      status: "erro_busca",
      erro: String(e),
    });
    return json({ erro: "falha ao buscar dataset no Apify", detalhe: String(e) }, 502);
  }

  if (itens.length === 0) {
    await db.from("apify_runs").upsert({
      run_id: runId,
      dataset_id: datasetId,
      status: "vazio",
      items_recebidos: 0,
    });
    return json({ ok: true, nota: "dataset vazio", run_id: runId });
  }

  // Entrega ao Postgres em blocos, para nao estourar payload.
  const bloco = 300;
  let ultimo: unknown = null;

  for (let i = 0; i < itens.length; i += bloco) {
    const { data, error } = await db.rpc("ingest_apify_items", {
      p_run_id: runId,
      p_dataset_id: datasetId,
      p_items: itens.slice(i, i + bloco),
    });
    if (error) {
      await db.from("apify_runs").upsert({
        run_id: runId,
        dataset_id: datasetId,
        status: "erro_ingest",
        erro: error.message,
      });
      return json({ erro: "falha no ingest", detalhe: error.message }, 500);
    }
    ultimo = data;
  }

  return json({ ok: true, run_id: runId, dataset_id: datasetId, resultado: ultimo });
});
