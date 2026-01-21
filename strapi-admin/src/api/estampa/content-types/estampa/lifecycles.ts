export default {
  async afterCreate(event: any) {
    const { result } = event;
    
    // Aguardar um pouco para garantir que o Strapi já criou o relacionamento na tabela de link
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Sincronizar categoria_id e tecido_id das tabelas de link para as colunas diretas
    if (result.id) {
      try {
        // Buscar categoria_id da tabela de link
        const categoriaLink = await strapi.db.connection.raw(
          `SELECT categoria_id FROM estampa_categoria_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (categoriaLink && categoriaLink.rows && categoriaLink.rows.length > 0) {
          const categoriaId = categoriaLink.rows[0].categoria_id;
          await strapi.db.connection.raw(
            `UPDATE estampa SET categoria_id = $1 WHERE id = $2`,
            [categoriaId, result.id]
          );
          strapi.log.info(`[LIFECYCLE] Estampa ${result.id}: categoria_id sincronizado para ${categoriaId}`);
        }
        
        // Buscar tecido_id da tabela de link
        const tecidoLink = await strapi.db.connection.raw(
          `SELECT tecido_id FROM estampa_tecido_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (tecidoLink && tecidoLink.rows && tecidoLink.rows.length > 0) {
          const tecidoId = tecidoLink.rows[0].tecido_id;
          await strapi.db.connection.raw(
            `UPDATE estampa SET tecido_id = $1 WHERE id = $2`,
            [tecidoId, result.id]
          );
          strapi.log.info(`[LIFECYCLE] Estampa ${result.id}: tecido_id sincronizado para ${tecidoId}`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao sincronizar colunas diretas:', error);
      }
    }
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    
    // Sincronizar categoria_id e tecido_id das tabelas de link para as colunas diretas
    if (result.id) {
      try {
        // Buscar categoria_id da tabela de link
        const categoriaLink = await strapi.db.connection.raw(
          `SELECT categoria_id FROM estampa_categoria_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (categoriaLink && categoriaLink.rows && categoriaLink.rows.length > 0) {
          const categoriaId = categoriaLink.rows[0].categoria_id;
          await strapi.db.connection.raw(
            `UPDATE estampa SET categoria_id = $1 WHERE id = $2`,
            [categoriaId, result.id]
          );
        } else {
          // Se não há link, remover categoria_id
          await strapi.db.connection.raw(
            `UPDATE estampa SET categoria_id = NULL WHERE id = $1`,
            [result.id]
          );
        }
        
        // Buscar tecido_id da tabela de link
        const tecidoLink = await strapi.db.connection.raw(
          `SELECT tecido_id FROM estampa_tecido_lnk WHERE estampa_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (tecidoLink && tecidoLink.rows && tecidoLink.rows.length > 0) {
          const tecidoId = tecidoLink.rows[0].tecido_id;
          await strapi.db.connection.raw(
            `UPDATE estampa SET tecido_id = $1 WHERE id = $2`,
            [tecidoId, result.id]
          );
        } else {
          await strapi.db.connection.raw(
            `UPDATE estampa SET tecido_id = NULL WHERE id = $1`,
            [result.id]
          );
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao sincronizar colunas diretas após update:', error);
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
