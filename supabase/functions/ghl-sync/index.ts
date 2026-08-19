// ghl-sync
// Leva os criadores aprovados do pool para o GHL: contato, tags e card.
//
// A logica de o-que-enviar vive em SQL (fila_sync_ghl / payload_ghl_contato).
// Aqui so tem o que precisa de rede: chamar a API do GHL na ordem certa,
// tratar falha item a item e fechar o ciclo no banco.
//
// O token do GHL vem do secret do projeto, ou do Vault se o secret nao
// existir. Ver a migration leitor_de_segredo_do_vault.
//
// POST { dry_run?: boolean, limite?: number, handles?: string[] }
//
// dry_run e TRUE por padrao. Sem `{"dry_run": false}` explicito nada e
// escrito no GHL — so devolve o que seria enviado. Isso e proposital:
// um card em Mapeado dispara o W5, que promove para Qualificado, que
// dispara o W7. Ver docs/ghl-inventario.md.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const GHL_BASE = "https://services.leadconnectorhq.com";
const GHL_VERSION = "2021-07-28";

// Tags aplicadas a todo criador que entra pelo pool.
// `afil-import` e o trigger previsto do W0 e serve de marca de procedencia.
const TAGS_ENTRADA = ["afiliado", "afil-import"];

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

type GhlResposta = { status: number; corpo: any };

// O token vem do secret do projeto se existir; senao, do Vault.
// A env var tem precedencia: quando o secret oficial for configurado no
// dashboard, ele passa a valer e o caminho do Vault vira peso morto.
async function resolverToken(db: any): Promise<string | null> {
  const doAmbiente = Deno.env.get("GHL_API_TOKEN");
  if (doAmbiente) return doAmbiente;

  const { data, error } = await db.rpc("segredo", { p_nome: "GHL_API_TOKEN" });
  if (error || !data) return null;
  return String(data);
}

async function ghl(
  token: string,
  metodo: string,
  caminho: string,
  corpo?: unknown,
): Promise<GhlResposta> {
  const r = await fetch(`${GHL_BASE}${caminho}`, {
    method: metodo,
    headers: {
      Authorization: `Bearer ${token}`,
      Version: GHL_VERSION,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });

  const texto = await r.text();
  let parsed: any = texto;
  try {
    parsed = texto ? JSON.parse(texto) : null;
  } catch {
    // deixa como texto: erro de gateway do GHL nem sempre volta JSON
  }
  return { status: r.status, corpo: parsed };
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ erro: "use POST" }, 405);

  const db = createClient(SUPABASE_URL, SERVICE_KEY);

  const token = await resolverToken(db);
  if (!token) {
    return json({
      erro: "GHL_API_TOKEN nao encontrado",
      onde_procurei: ["secret do projeto", "vault (rpc segredo)"],
    }, 500);
  }

  let entrada: any = {};
  if (req.headers.get("content-length") !== "0") {
    try {
      entrada = await req.json();
    } catch {
      return json({ erro: "corpo nao e JSON valido" }, 400);
    }
  }

  // Precisa dizer dry_run: false na mao. Qualquer outra coisa e ensaio.
  const dryRun = entrada?.dry_run !== false;
  const limite = Math.min(Number(entrada?.limite ?? 10), 100);
  const handles: string[] | null = Array.isArray(entrada?.handles)
    ? entrada.handles
    : null;

  let q = db
    .from("fila_sync_ghl")
    .select("handle, status, nickname, email, fans, trilha, stage_id, opportunity_name, payload");

  if (handles) q = q.in("handle", handles);
  else q = q.limit(limite);

  const { data: fila, error: erroFila } = await q;

  if (erroFila) {
    return json({ erro: "falha ao ler a fila", detalhe: erroFila.message }, 500);
  }
  if (!fila || fila.length === 0) {
    return json({ ok: true, nota: "fila vazia, nada a enviar", enviados: 0 });
  }

  const { data: cfg } = await db
    .from("ghl_config")
    .select("chave, valor");
  const config = Object.fromEntries((cfg ?? []).map((r: any) => [r.chave, r.valor]));
  const pipelineId = config["pipeline_jornada"];

  if (!pipelineId) {
    return json({ erro: "pipeline_jornada ausente em ghl_config" }, 500);
  }

  if (dryRun) {
    return json({
      ok: true,
      dry_run: true,
      nota:
        "nada foi escrito no GHL. Para valer, mande {\"dry_run\": false}. " +
        "Antes disso confira o estado do W7: card em Mapeado vira Qualificado pelo W5 e cai na sequencia de e-mail.",
      seriam_enviados: fila.length,
      pipeline: pipelineId,
      itens: fila.map((f: any) => ({
        handle: f.handle,
        status: f.status,
        email: f.email,
        stage_id: f.stage_id,
        opportunity_name: f.opportunity_name,
        tags: TAGS_ENTRADA,
        payload: f.payload,
      })),
    });
  }

  const resultado: any[] = [];

  for (const item of fila) {
    const passo = { handle: item.handle, ok: false } as any;

    // 1) contato. Upsert porque o criador pode ja existir na base como
    //    outra coisa (cliente B2B, lead antigo).
    const up = await ghl(token, "POST", "/contacts/upsert", item.payload);
    const contactId = up.corpo?.contact?.id ?? up.corpo?.id;

    if (up.status >= 300 || !contactId) {
      await db.rpc("registrar_falha_sync", {
        p_handle: item.handle,
        p_acao: "contato",
        p_status: up.status,
        p_erro: JSON.stringify(up.corpo).slice(0, 2000),
        p_payload: item.payload,
      });
      resultado.push({ ...passo, etapa: "contato", http: up.status, erro: up.corpo });
      continue;
    }

    passo.ghl_contact_id = contactId;
    passo.contato_novo = up.corpo?.new ?? null;

    // 2) tags por endpoint separado, porque o campo `tags` do upsert
    //    substitui todas as tags existentes do contato.
    const tg = await ghl(token, "POST", `/contacts/${contactId}/tags`, { tags: TAGS_ENTRADA });
    passo.tags_http = tg.status;

    if (tg.status >= 300) {
      // Nao aborta: contato criado sem tag ainda e recuperavel, e o card
      // e mais importante para o fluxo. Fica registrado.
      await db.rpc("registrar_falha_sync", {
        p_handle: item.handle,
        p_acao: "tags",
        p_status: tg.status,
        p_erro: JSON.stringify(tg.corpo).slice(0, 2000),
        p_payload: { tags: TAGS_ENTRADA },
      });
    }

    // 3) card na jornada.
    const opBody = {
      pipelineId,
      pipelineStageId: item.stage_id,
      name: item.opportunity_name,
      status: "open",
      contactId,
      monetaryValue: 0,
    };
    const op = await ghl(token, "POST", "/opportunities/upsert", opBody);
    const oppId = op.corpo?.opportunity?.id ?? op.corpo?.id;

    if (op.status >= 300 || !oppId) {
      await db.rpc("registrar_falha_sync", {
        p_handle: item.handle,
        p_acao: "card",
        p_status: op.status,
        p_erro: JSON.stringify(op.corpo).slice(0, 2000),
        p_payload: opBody,
      });
      // O contato existe. Nao marca como sincronizado para a proxima
      // rodada tentar de novo — o upsert nao duplica.
      resultado.push({ ...passo, etapa: "card", http: op.status, erro: op.corpo });
      continue;
    }

    passo.ghl_opportunity_id = oppId;

    // 4) fecha o ciclo no banco.
    const { error: erroMarca } = await db.rpc("marcar_sincronizado", {
      p_handle: item.handle,
      p_contact_id: contactId,
      p_opportunity_id: oppId,
      p_payload: item.payload,
    });

    if (erroMarca) {
      resultado.push({ ...passo, etapa: "marcar", erro: erroMarca.message });
      continue;
    }

    passo.ok = true;
    resultado.push(passo);
  }

  const ok = resultado.filter((r) => r.ok).length;

  return json({
    ok: true,
    dry_run: false,
    enviados: ok,
    falhas: resultado.length - ok,
    detalhe: resultado,
  });
});
