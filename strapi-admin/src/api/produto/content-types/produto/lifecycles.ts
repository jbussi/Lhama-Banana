export default {
  async afterCreate(event: any) {
    const { result } = event;
    
    // Aguardar um pouco para garantir que o Strapi já criou o relacionamento na tabela de link
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Sincronizar nome_produto_id, estampa_id e tamanho_id das tabelas de link para as colunas diretas
    if (result.id) {
      try {
        // Buscar nome_produto_id da tabela de link
        const nomeProdutoLink = await strapi.db.connection.raw(
          `SELECT nome_produto_id FROM produtos_nome_produto_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (nomeProdutoLink && nomeProdutoLink.rows && nomeProdutoLink.rows.length > 0) {
          const nomeProdutoId = nomeProdutoLink.rows[0].nome_produto_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET nome_produto_id = $1 WHERE id = $2`,
            [nomeProdutoId, result.id]
          );
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: nome_produto_id sincronizado para ${nomeProdutoId}`);
        }
        
        // Buscar estampa_id da tabela de link
        const estampaLink = await strapi.db.connection.raw(
          `SELECT estampa_id FROM produtos_estampa_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (estampaLink && estampaLink.rows && estampaLink.rows.length > 0) {
          const estampaId = estampaLink.rows[0].estampa_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET estampa_id = $1 WHERE id = $2`,
            [estampaId, result.id]
          );
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: estampa_id sincronizado para ${estampaId}`);
        }
        
        // Buscar tamanho_id da tabela de link
        const tamanhoLink = await strapi.db.connection.raw(
          `SELECT tamanho_id FROM produtos_tamanho_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (tamanhoLink && tamanhoLink.rows && tamanhoLink.rows.length > 0) {
          const tamanhoId = tamanhoLink.rows[0].tamanho_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET tamanho_id = $1 WHERE id = $2`,
            [tamanhoId, result.id]
          );
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: tamanho_id sincronizado para ${tamanhoId}`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao sincronizar colunas diretas:', error);
      }
    }
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    
    // Sincronizar nome_produto_id, estampa_id e tamanho_id das tabelas de link para as colunas diretas
    if (result.id) {
      try {
        // Buscar nome_produto_id da tabela de link
        const nomeProdutoLink = await strapi.db.connection.raw(
          `SELECT nome_produto_id FROM produtos_nome_produto_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (nomeProdutoLink && nomeProdutoLink.rows && nomeProdutoLink.rows.length > 0) {
          const nomeProdutoId = nomeProdutoLink.rows[0].nome_produto_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET nome_produto_id = $1 WHERE id = $2`,
            [nomeProdutoId, result.id]
          );
        } else {
          await strapi.db.connection.raw(
            `UPDATE produtos SET nome_produto_id = NULL WHERE id = $1`,
            [result.id]
          );
        }
        
        // Buscar estampa_id da tabela de link
        const estampaLink = await strapi.db.connection.raw(
          `SELECT estampa_id FROM produtos_estampa_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (estampaLink && estampaLink.rows && estampaLink.rows.length > 0) {
          const estampaId = estampaLink.rows[0].estampa_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET estampa_id = $1 WHERE id = $2`,
            [estampaId, result.id]
          );
        } else {
          await strapi.db.connection.raw(
            `UPDATE produtos SET estampa_id = NULL WHERE id = $1`,
            [result.id]
          );
        }
        
        // Buscar tamanho_id da tabela de link
        const tamanhoLink = await strapi.db.connection.raw(
          `SELECT tamanho_id FROM produtos_tamanho_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        
        if (tamanhoLink && tamanhoLink.rows && tamanhoLink.rows.length > 0) {
          const tamanhoId = tamanhoLink.rows[0].tamanho_id;
          await strapi.db.connection.raw(
            `UPDATE produtos SET tamanho_id = $1 WHERE id = $2`,
            [tamanhoId, result.id]
          );
        } else {
          await strapi.db.connection.raw(
            `UPDATE produtos SET tamanho_id = NULL WHERE id = $1`,
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
        `DELETE FROM produtos_nome_produto_lnk WHERE produto_id = $1`,
        [result.id]
      );
      await strapi.db.connection.raw(
        `DELETE FROM produtos_estampa_lnk WHERE produto_id = $1`,
        [result.id]
      );
      await strapi.db.connection.raw(
        `DELETE FROM produtos_tamanho_lnk WHERE produto_id = $1`,
        [result.id]
      );
    }
  },
};
