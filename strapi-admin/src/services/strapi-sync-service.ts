/**
 * Serviço de Sincronização Strapi -> PostgreSQL
 * ==============================================
 * 
 * Sincroniza automaticamente os content types do Strapi com as tabelas do PostgreSQL
 * quando há criação, atualização ou exclusão de conteúdo.
 */

import { Pool } from 'pg';

// Configuração do banco de dados PostgreSQL
// Usa as mesmas variáveis de ambiente do Strapi
const getPostgresConfig = () => {
  return {
    host: process.env.DATABASE_HOST || 'postgres',
    port: parseInt(process.env.DATABASE_PORT || '5432'),
    database: process.env.DATABASE_NAME || 'sistema_usuarios',
    user: process.env.DATABASE_USERNAME || 'postgres',
    password: process.env.DATABASE_PASSWORD || 'postgres',
  };
};

// Pool de conexões PostgreSQL
let pgPool: Pool | null = null;

const getPostgresPool = (): Pool => {
  if (!pgPool) {
    const config = getPostgresConfig();
    pgPool = new Pool({
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      max: 5,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
    
    pgPool.on('error', (err) => {
      strapi.log.error('Erro inesperado no pool PostgreSQL:', err);
    });
  }
  return pgPool;
};

/**
 * Processa URL de imagem do Strapi para URL completa
 */
const processImageUrl = (image: any): string | null => {
  if (!image) return null;
  
  if (typeof image === 'string') {
    return image;
  }
  
  if (image && typeof image === 'object') {
    // Se for um objeto com url
    if (image.url) {
      const baseUrl = process.env.PUBLIC_URL || process.env.STRAPI_URL || 'http://localhost:1337';
      return image.url.startsWith('http') ? image.url : `${baseUrl}${image.url}`;
    }
    
    // Se for um array (múltiplas imagens), pegar a primeira
    if (Array.isArray(image) && image.length > 0) {
      const firstImage = image[0];
      if (firstImage && firstImage.url) {
        const baseUrl = process.env.PUBLIC_URL || process.env.STRAPI_URL || 'http://localhost:1337';
        return firstImage.url.startsWith('http') ? firstImage.url : `${baseUrl}${firstImage.url}`;
      }
    }
  }
  
  return null;
};

/**
 * Sincroniza Conteúdo Home do Strapi para PostgreSQL
 */
export const syncConteudoHomeToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    // Processar hero_imagem
    const hero_imagem_url = data.hero_imagem ? processImageUrl(data.hero_imagem) : null;
    
    // Processar carrosséis e depoimentos (já devem vir como JSON do Strapi)
    const carrosseis = data.carrosseis ? JSON.stringify(data.carrosseis) : '[]';
    const depoimentos = data.depoimentos ? JSON.stringify(data.depoimentos) : '[]';
    
    // Sempre usar o primeiro registro (ID mais antigo) ou criar se não existir
    // Isso evita múltiplos registros duplicados
    const checkResult = await pool.query(
      'SELECT id FROM conteudo_home ORDER BY id ASC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      // Sempre atualizar o mesmo registro (ID mais antigo)
      // Desativar outros registros se existirem
      await pool.query('UPDATE conteudo_home SET ativo = FALSE WHERE id != $1', [checkResult.rows[0].id]);
      
      await pool.query(`
        UPDATE conteudo_home SET
          hero_titulo = $1,
          hero_subtitulo = $2,
          hero_imagem_url = $3,
          hero_texto_botao = $4,
          carrosseis = $5::jsonb,
          depoimentos = $6::jsonb,
          estatisticas_clientes = $7,
          estatisticas_pecas = $8,
          estatisticas_anos = $9,
          ativo = $10,
          atualizado_em = NOW()
        WHERE id = $11
      `, [
        data.hero_titulo || null,
        data.hero_subtitulo || null,
        hero_imagem_url,
        data.hero_texto_botao || 'Comprar Agora',
        carrosseis,
        depoimentos,
        data.estatisticas_clientes || 5000,
        data.estatisticas_pecas || 10000,
        data.estatisticas_anos || 5,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Home atualizado no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      // Criar novo registro apenas se não existir nenhum
      const insertResult = await pool.query(`
        INSERT INTO conteudo_home (
          hero_titulo, hero_subtitulo, hero_imagem_url, hero_texto_botao,
          carrosseis, depoimentos, estatisticas_clientes, estatisticas_pecas, estatisticas_anos,
          ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, $10, NOW(), NOW())
        RETURNING id
      `, [
        data.hero_titulo || null,
        data.hero_subtitulo || null,
        hero_imagem_url,
        data.hero_texto_botao || 'Comprar Agora',
        carrosseis,
        depoimentos,
        data.estatisticas_clientes || 5000,
        data.estatisticas_pecas || 10000,
        data.estatisticas_anos || 5,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Home criado no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Conteudo Home:', error);
    throw error;
  }
};

/**
 * Sincroniza Informações da Empresa do Strapi para PostgreSQL
 */
export const syncInformacoesEmpresaToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    const valores = data.valores ? JSON.stringify(data.valores) : '[]';
    const redes_sociais = data.redes_sociais ? JSON.stringify(data.redes_sociais) : '{}';
    
    const checkResult = await pool.query(
      'SELECT id FROM informacoes_empresa WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE informacoes_empresa SET
          email = $1,
          telefone = $2,
          whatsapp = $3,
          horario_atendimento = $4,
          valores = $5::jsonb,
          redes_sociais = $6::jsonb,
          ativo = $7,
          atualizado_em = NOW()
        WHERE id = $8
      `, [
        data.email || null,
        data.telefone || null,
        data.whatsapp || null,
        data.horario_atendimento || null,
        valores,
        redes_sociais,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Informações Empresa atualizadas no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO informacoes_empresa (
          email, telefone, whatsapp, horario_atendimento,
          valores, redes_sociais, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, NOW(), NOW())
        RETURNING id
      `, [
        data.email || null,
        data.telefone || null,
        data.whatsapp || null,
        data.horario_atendimento || null,
        valores,
        redes_sociais,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Informações Empresa criadas no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Informações Empresa:', error);
    throw error;
  }
};

/**
 * Sincroniza Conteúdo Sobre do Strapi para PostgreSQL
 */
export const syncConteudoSobreToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    // Converter richtext para texto simples se necessário
    const historia_conteudo = typeof data.historia_conteudo === 'string' 
      ? data.historia_conteudo 
      : (data.historia_conteudo?.text || null);
    
    const valores_conteudo = data.valores_conteudo ? JSON.stringify(data.valores_conteudo) : '[]';
    const equipe_conteudo = data.equipe ? JSON.stringify(data.equipe) : '[]';
    
    const checkResult = await pool.query(
      'SELECT id FROM conteudo_sobre WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE conteudo_sobre SET
          historia_titulo = $1,
          historia_conteudo = $2,
          valores_titulo = $3,
          valores_conteudo = $4::jsonb,
          equipe_titulo = $5,
          equipe_conteudo = $6::jsonb,
          ativo = $7,
          atualizado_em = NOW()
        WHERE id = $8
      `, [
        data.historia_titulo || 'Nossa História',
        historia_conteudo,
        data.valores_titulo || 'Nossos Valores',
        valores_conteudo,
        data.equipe_titulo || 'Nossa Equipe',
        equipe_conteudo,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Sobre atualizado no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO conteudo_sobre (
          historia_titulo, historia_conteudo, valores_titulo, valores_conteudo,
          equipe_titulo, equipe_conteudo, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb, $7, NOW(), NOW())
        RETURNING id
      `, [
        data.historia_titulo || 'Nossa História',
        historia_conteudo,
        data.valores_titulo || 'Nossos Valores',
        valores_conteudo,
        data.equipe_titulo || 'Nossa Equipe',
        equipe_conteudo,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Sobre criado no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Conteudo Sobre:', error);
    throw error;
  }
};

/**
 * Sincroniza Conteúdo Contato do Strapi para PostgreSQL
 */
export const syncConteudoContatoToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    const texto_principal = typeof data.texto_principal === 'string'
      ? data.texto_principal
      : (data.texto_principal?.text || null);
    
    const informacoes = data.informacoes_contato ? JSON.stringify(data.informacoes_contato) : '[]';
    const links = data.redes_sociais ? JSON.stringify(data.redes_sociais) : '{}';
    
    const checkResult = await pool.query(
      'SELECT id FROM conteudo_contato WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE conteudo_contato SET
          titulo = $1,
          texto_principal = $2,
          informacoes = $3::jsonb,
          links = $4::jsonb,
          form_titulo = $5,
          form_texto = $6,
          ativo = $7,
          atualizado_em = NOW()
        WHERE id = $8
      `, [
        data.titulo || 'Entre em Contato',
        texto_principal,
        informacoes,
        links,
        data.form_titulo || null,
        data.form_texto || null,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Contato atualizado no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO conteudo_contato (
          titulo, texto_principal, informacoes, links,
          form_titulo, form_texto, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7, NOW(), NOW())
        RETURNING id
      `, [
        data.titulo || 'Entre em Contato',
        texto_principal,
        informacoes,
        links,
        data.form_titulo || null,
        data.form_texto || null,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Conteudo Contato criado no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Conteudo Contato:', error);
    throw error;
  }
};

/**
 * Sincroniza Política de Privacidade do Strapi para PostgreSQL
 */
export const syncPoliticaPrivacidadeToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const checkResult = await pool.query(
      'SELECT id FROM politica_privacidade WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE politica_privacidade SET
          titulo = $1,
          ultima_atualizacao = $2,
          conteudo = $3,
          secoes = $4::jsonb,
          ativo = $5,
          atualizado_em = NOW()
        WHERE id = $6
      `, [
        data.titulo || 'Política de Privacidade',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Política de Privacidade atualizada no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO politica_privacidade (
          titulo, ultima_atualizacao, conteudo, secoes, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW(), NOW())
        RETURNING id
      `, [
        data.titulo || 'Política de Privacidade',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Política de Privacidade criada no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Política de Privacidade:', error);
    throw error;
  }
};

/**
 * Sincroniza Política de Envio do Strapi para PostgreSQL
 */
export const syncPoliticaEnvioToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const checkResult = await pool.query(
      'SELECT id FROM politica_envio WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE politica_envio SET
          titulo = $1,
          ultima_atualizacao = $2,
          conteudo = $3,
          secoes = $4::jsonb,
          ativo = $5,
          atualizado_em = NOW()
        WHERE id = $6
      `, [
        data.titulo || 'Política de Envio',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Política de Envio atualizada no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO politica_envio (
          titulo, ultima_atualizacao, conteudo, secoes, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW(), NOW())
        RETURNING id
      `, [
        data.titulo || 'Política de Envio',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Política de Envio criada no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Política de Envio:', error);
    throw error;
  }
};

/**
 * Sincroniza Direitos Reservados do Strapi para PostgreSQL
 */
export const syncDireitosReservadosToPostgres = async (data: any) => {
  try {
    const pool = getPostgresPool();
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const checkResult = await pool.query(
      'SELECT id FROM direitos_reservados WHERE ativo = TRUE ORDER BY id DESC LIMIT 1'
    );
    
    if (checkResult.rows.length > 0) {
      await pool.query(`
        UPDATE direitos_reservados SET
          titulo = $1,
          ultima_atualizacao = $2,
          conteudo = $3,
          secoes = $4::jsonb,
          ativo = $5,
          atualizado_em = NOW()
        WHERE id = $6
      `, [
        data.titulo || 'Todos os Direitos Reservados',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false,
        checkResult.rows[0].id
      ]);
      
      strapi.log.info(`[SYNC] Direitos Reservados atualizado no PostgreSQL (ID: ${checkResult.rows[0].id})`);
    } else {
      const insertResult = await pool.query(`
        INSERT INTO direitos_reservados (
          titulo, ultima_atualizacao, conteudo, secoes, ativo, criado_em, atualizado_em
        ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW(), NOW())
        RETURNING id
      `, [
        data.titulo || 'Todos os Direitos Reservados',
        data.ultima_atualizacao || null,
        conteudo,
        secoes,
        data.ativo !== false
      ]);
      
      strapi.log.info(`[SYNC] Direitos Reservados criado no PostgreSQL (ID: ${insertResult.rows[0].id})`);
    }
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Direitos Reservados:', error);
    throw error;
  }
};
