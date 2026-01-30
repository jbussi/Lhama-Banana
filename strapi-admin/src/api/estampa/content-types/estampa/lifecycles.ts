export default {
  async afterCreate(event: any) {
    const { result } = event;
    
    // Aguardar um pouco para garantir que o Strapi já criou o relacionamento na tabela de link
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Verificar se as tabelas de link foram criadas corretamente
    if (result.id) {
      try {
        // Verificar categoria
        const categoriaLink = await strapi.db.connection.raw(
          `SELECT categoria_id FROM estampa_categoria_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        if (categoriaLink && categoriaLink.rows && categoriaLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Estampa ${result.id}: Relacionamento com categoria criado`);
        }
        
        // Verificar tecido
        const tecidoLink = await strapi.db.connection.raw(
          `SELECT tecido_id FROM estampa_tecido_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        if (tecidoLink && tecidoLink.rows && tecidoLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Estampa ${result.id}: Relacionamento com tecido criado`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar relacionamentos da estampa:', error);
      }
    }
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    
    // Verificar se as tabelas de link foram atualizadas corretamente
    if (result.id) {
      try {
        strapi.log.info(`[LIFECYCLE] Estampa ${result.id}: Atualizada com sucesso`);
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar atualização da estampa:', error);
      }
    }
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    
    // Limpar tabelas de link quando deletar
    if (result.id) {
      await strapi.db.connection.raw(
        `DELETE FROM estampa_categoria_lnk WHERE estampa_id = $1`,
        [result.id]
      );
      await strapi.db.connection.raw(
        `DELETE FROM estampa_tecido_lnk WHERE estampa_id = $1`,
        [result.id]
      );
    }
  },
};
