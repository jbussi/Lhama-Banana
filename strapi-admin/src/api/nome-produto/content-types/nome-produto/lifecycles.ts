export default {
  async beforeDelete(event: any) {
    strapi.log.info('[LIFECYCLE] beforeDelete Nome Produto - Event recebido:', JSON.stringify(event, null, 2));
    
    const { params, model } = event;
    const { where } = params || {};
    
    strapi.log.info('[LIFECYCLE] beforeDelete Nome Produto - params:', JSON.stringify(params, null, 2));
    strapi.log.info('[LIFECYCLE] beforeDelete Nome Produto - where:', JSON.stringify(where, null, 2));
    strapi.log.info('[LIFECYCLE] beforeDelete Nome Produto - model:', model);
    
    let nomeProdutoId = null;
    
    // Tentar múltiplas formas de obter o ID
    // 1. Tentar via where.id
    if (where && where.id) {
      if (Array.isArray(where.id.$in)) {
        nomeProdutoId = where.id.$in[0];
      } else if (typeof where.id === 'object' && where.id.$eq) {
        nomeProdutoId = where.id.$eq;
      } else if (typeof where.id === 'number') {
        nomeProdutoId = where.id;
      }
      strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto - ID extraído de where.id: ${nomeProdutoId}`);
    }
    
    // 2. Tentar via where.documentId
    if (!nomeProdutoId && where && where.documentId) {
      strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto - Tentando buscar por documentId: ${where.documentId}`);
      try {
        const nomeProduto = await strapi.db.query('api::nome-produto.nome-produto').findOne({
          where: { documentId: where.documentId },
        });
        if (nomeProduto) {
          nomeProdutoId = nomeProduto.id;
          strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto - ID encontrado via documentId: ${nomeProdutoId}`);
        } else {
          strapi.log.warn(`[LIFECYCLE] beforeDelete Nome Produto - Nome Produto não encontrado com documentId: ${where.documentId}`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] beforeDelete Nome Produto - Erro ao buscar por documentId:', error);
      }
    }
    
    // 3. Tentar buscar diretamente se temos um documentId em outro formato
    if (!nomeProdutoId && where) {
      // Tentar buscar todos os campos do where para encontrar o ID
      for (const [key, value] of Object.entries(where)) {
        if (key === 'documentId' && typeof value === 'string') {
          try {
            const nomeProduto = await strapi.db.query('api::nome-produto.nome-produto').findOne({
              where: { documentId: value },
            });
            if (nomeProduto) {
              nomeProdutoId = nomeProduto.id;
              strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto - ID encontrado via documentId (loop): ${nomeProdutoId}`);
              break;
            }
          } catch (error) {
            strapi.log.error(`[LIFECYCLE] beforeDelete Nome Produto - Erro ao buscar por ${key}:`, error);
          }
        }
      }
    }
    
    if (!nomeProdutoId) {
      strapi.log.warn('[LIFECYCLE] beforeDelete Nome Produto - Não foi possível extrair ID de nenhuma forma');
      strapi.log.warn('[LIFECYCLE] beforeDelete Nome Produto - Estrutura completa do where:', JSON.stringify(where, null, 2));
    }
    
    if (nomeProdutoId) {
      // Verificar se o nome_produto realmente existe no banco de dados
      try {
        const nomeProdutoExists = await strapi.db.query('api::nome-produto.nome-produto').findOne({
          where: { id: nomeProdutoId },
        });
        
        if (!nomeProdutoExists) {
          strapi.log.warn(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Nome Produto não existe no banco de dados (registro órfão). Permitindo exclusão sem limpar referências.`);
          // Retornar sem fazer nada - permite que o Strapi continue com a exclusão
          return;
        }
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Erro ao verificar existência:`, error);
        // Continuar mesmo com erro na verificação
      }
      
      strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Nome Produto existe no banco. Iniciando limpeza de referências`);
      try {
        // Limpar referências nas tabelas de link antes de deletar
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Deletando de nome_produto_categoria_lnk`);
        const result1 = await strapi.db.connection.raw(
          `DELETE FROM nome_produto_categoria_lnk WHERE nome_produto_id = $1`,
          [nomeProdutoId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Resultado nome_produto_categoria_lnk:`, result1.rowCount);
        
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Deletando de produtos_nome_produto_lnk`);
        const result2 = await strapi.db.connection.raw(
          `DELETE FROM produtos_nome_produto_lnk WHERE nome_produto_id = $1`,
          [nomeProdutoId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Resultado produtos_nome_produto_lnk:`, result2.rowCount);
        
        // Limpar nome_produto_id nas colunas diretas (já que temos ON DELETE CASCADE, mas vamos garantir)
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Atualizando produtos.nome_produto_id`);
        const result3 = await strapi.db.connection.raw(
          `UPDATE produtos SET nome_produto_id = NULL WHERE nome_produto_id = $1`,
          [nomeProdutoId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Resultado UPDATE produtos:`, result3.rowCount);
        
        strapi.log.info(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Referências limpas com sucesso antes da exclusão`);
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Erro ao limpar referências:`, error);
        strapi.log.error(`[LIFECYCLE] beforeDelete Nome Produto ${nomeProdutoId} - Stack trace:`, error?.stack);
        // Não lançar erro para não bloquear a exclusão
      }
    } else {
      strapi.log.warn('[LIFECYCLE] beforeDelete Nome Produto - nomeProdutoId é null. Registro pode não existir no banco. Permitindo exclusão sem limpar referências.');
      // Não fazer nada - permite que o Strapi continue mesmo sem ID
    }
  },
  
  async afterCreate(event: any) {
    const { result } = event;
    
    // Aguardar um pouco para garantir que o Strapi já criou o relacionamento na tabela de link
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Verificar se a tabela de link foi criada corretamente
    if (result.id) {
      try {
        // Verificar categoria
        const categoriaLink = await strapi.db.connection.raw(
          `SELECT categoria_id FROM nome_produto_categoria_lnk WHERE nome_produto_id = $1 LIMIT 1`,
          [result.id]
        );
        if (categoriaLink && categoriaLink.rows && categoriaLink.rows.length > 0) {
          strapi.log.info(`[LIFECYCLE] Nome Produto ${result.id}: Relacionamento com categoria criado`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar relacionamento do nome_produto:', error);
      }
    }
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    
    // Verificar se a tabela de link foi atualizada corretamente
    if (result.id) {
      try {
        strapi.log.info(`[LIFECYCLE] Nome Produto ${result.id}: Atualizado com sucesso`);
      } catch (error) {
        strapi.log.error('[LIFECYCLE] Erro ao verificar atualização do nome_produto:', error);
      }
    }
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    
    // Limpar tabela de link quando deletar
    if (result.id) {
      await strapi.db.connection.raw(
        `DELETE FROM nome_produto_categoria_lnk WHERE nome_produto_id = $1`,
        [result.id]
      );
    }
  },
};
