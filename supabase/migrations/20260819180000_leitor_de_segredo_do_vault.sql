-- Leitor de segredo do Vault, para a Edge Function nao depender de env var.
--
-- O segredo em si NAO esta neste arquivo nem em lugar nenhum do git. Ele e
-- inserido fora de banda, uma vez, por quem tem a credencial:
--
--   select vault.create_secret('<valor>', 'GHL_API_TOKEN', 'descricao');
--
-- Para trocar depois:
--   select vault.update_secret(
--     (select id from vault.secrets where name = 'GHL_API_TOKEN'),
--     '<valor novo>');
--
-- SECURITY DEFINER porque vault.decrypted_secrets nao e legivel pela
-- service_role direto, e o schema vault nao e exposto pela Data API.
-- O grant e so para service_role: anon e authenticated nunca chegam aqui.
create or replace function public.segredo(p_nome text)
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select s.decrypted_secret
  from vault.decrypted_secrets s
  where s.name = p_nome
  limit 1;
$$;

comment on function public.segredo is 'Le um segredo do Vault. Exclusivo da service_role. Ver o cabecalho da migration para como inserir e rotacionar.';

revoke all on function public.segredo(text) from public, anon, authenticated;
grant execute on function public.segredo(text) to service_role;
