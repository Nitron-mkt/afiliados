-- O linter de seguranca aponta rls_auto_enable() como SECURITY DEFINER
-- executavel por anon e authenticated via /rest/v1/rpc/.
--
-- Na pratica ela e a funcao do event trigger `ensure_rls` e retorna
-- event_trigger, entao chamar por RPC ja falharia. Mas grant que nao
-- precisa existir e grant que sai. Revogar nao afeta o event trigger:
-- event trigger roda como dono, sem consultar EXECUTE.
revoke all on function public.rls_auto_enable() from anon, authenticated, public;
