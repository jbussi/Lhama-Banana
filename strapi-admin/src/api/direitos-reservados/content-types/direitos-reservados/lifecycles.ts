import { syncDireitosReservadosToPostgres } from '../../../../services/strapi-sync-service';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Direitos Reservados criado: ${result.id}`);
    await syncDireitosReservadosToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Direitos Reservados atualizado: ${result.id}`);
    await syncDireitosReservadosToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Direitos Reservados deletado: ${result.id}`);
    await syncDireitosReservadosToPostgres({ ...result, ativo: false });
  }
};
