import { syncConteudoContatoToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato criado: ${result.id}`);
    await syncConteudoContatoToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato atualizado: ${result.id}`);
    await syncConteudoContatoToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato deletado: ${result.id}`);
    await syncConteudoContatoToPostgres({ ...result, ativo: false });
  }
};
