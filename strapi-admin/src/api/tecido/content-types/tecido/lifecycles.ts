export default {
  async afterDelete(event: any) {
    const { result } = event;
    
    // Limpar tabela de link quando deletar
    if (result.id) {
      try {
        await strapi.db.connection.raw(
          `DELETE FROM estampa_tecido_lnk WHERE tecido_id = $1`,
          [result.id]
        );
        strapi.log.info(`[LIFECYCLE] Tecido ${result.id}: Referências limpas`);
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] Erro ao limpar referências do tecido ${result.id}:`, error);
      }
    }
  },
};
