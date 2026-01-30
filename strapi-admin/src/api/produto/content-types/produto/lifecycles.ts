export default {
  async afterCreate(event: any) {
    const { result } = event;
    
    // Aguardar um pouco para garantir que o Strapi já criou o relacionamento na tabela de link
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Verificar se as tabelas de link foram criadas corretamente
    if (result.id) {
      try {
        // Verificar nome_produto
        const nomeProdutoLink = await strapi.db.connection.raw(
          `SELECT nome_produto_id FROM produtos_nome_produto_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        if (nomeProdutoLink && nomeProdutoLink.rows && nomeProdutoLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: Relacionamento com nome_produto criado`);
        }
        
        // Verificar estampa
        const estampaLink = await strapi.db.connection.raw(
          `SELECT estampa_id FROM produtos_estampa_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        if (estampaLink && estampaLink.rows && estampaLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: Relacionamento com estampa criado`);
        }
        
        // Verificar tamanho
        const tamanhoLink = await strapi.db.connection.raw(
          `SELECT tamanho_id FROM produtos_tamanho_lnk WHERE produto_id = $1 LIMIT 1`,
          [result.id]
        );
        if (tamanhoLink && tamanhoLink.rows && tamanhoLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Produto ${result.id}: Relacionamento com tamanho criado`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar relacionamentos do produto:', error);
      }
    }
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    
    // Verificar se as tabelas de link foram atualizadas corretamente
    if (result.id) {
      try {
        strapi.log.info(`[LIFECYCLE] Produto ${result.id}: Atualizado com sucesso`);
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar atualização do produto:', error);
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
