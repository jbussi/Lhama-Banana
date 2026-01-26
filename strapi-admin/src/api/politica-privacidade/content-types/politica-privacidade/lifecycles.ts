import { syncPoliticaPrivacidadeToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Privacidade criada: ${result.id}`);
    await syncPoliticaPrivacidadeToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Privacidade atualizada: ${result.id}`);
    await syncPoliticaPrivacidadeToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Privacidade deletada: ${result.id}`);
    await syncPoliticaPrivacidadeToPostgres({ ...result, ativo: false });
  }
};
