import { syncPoliticaEnvioToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Envio criada: ${result.id}`);
    await syncPoliticaEnvioToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Envio atualizada: ${result.id}`);
    await syncPoliticaEnvioToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Política de Envio deletada: ${result.id}`);
    await syncPoliticaEnvioToPostgres({ ...result, ativo: false });
  }
};
