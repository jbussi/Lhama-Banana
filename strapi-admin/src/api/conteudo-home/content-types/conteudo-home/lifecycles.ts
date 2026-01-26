import { syncConteudoHomeToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Home criado: ${result.id}`);
    await syncConteudoHomeToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Home atualizado: ${result.id}`);
    await syncConteudoHomeToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Home deletado: ${result.id}`);
    await syncConteudoHomeToPostgres({ ...result, ativo: false });
  }
};
