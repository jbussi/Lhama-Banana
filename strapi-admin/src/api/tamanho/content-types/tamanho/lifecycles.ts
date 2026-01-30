export default {
  async afterDelete(event: any) {
    const { result } = event;
    
    // Limpar tabela de link quando deletar
    if (result.id) {
      try {
        await strapi.db.connection.raw(
          `DELETE FROM produtos_tamanho_lnk WHERE tamanho_id = $1`,
          [result.id]
        );
        strapi.log.info(`[LIFECYCLE] Tamanho ${result.id}: Referências limpas`);
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] Erro ao limpar referências do tamanho ${result.id}:`, error);
      }
    }
  },
};
