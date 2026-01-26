import { syncConteudoSobreToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Sobre criado: ${result.id}`);
    await syncConteudoSobreToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Sobre atualizado: ${result.id}`);
    await syncConteudoSobreToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Sobre deletado: ${result.id}`);
    await syncConteudoSobreToPostgres({ ...result, ativo: false });
  }
};
