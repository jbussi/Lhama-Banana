import { syncInformacoesEmpresaToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Informações Empresa criadas: ${result.id}`);
    await syncInformacoesEmpresaToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Informações Empresa atualizadas: ${result.id}`);
    await syncInformacoesEmpresaToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Informações Empresa deletadas: ${result.id}`);
    await syncInformacoesEmpresaToPostgres({ ...result, ativo: false });
  }
};
