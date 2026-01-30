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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    // Processar hero_imagem
    const hero_imagem_url = data.hero_imagem ? processImageUrl(data.hero_imagem) : null;
    
    // Processar carrosséis e depoimentos (já devem vir como JSON do Strapi)
    const carrosseis = data.carrosseis ? JSON.stringify(data.carrosseis) : '[]';
    const depoimentos = data.depoimentos ? JSON.stringify(data.depoimentos) : '[]';
    
    // IMPORTANTE: não escrever nas tabelas internas do Strapi (ex.: conteudo_home),
    // senão criamos duplicação/loops. Escrevemos na tabela espelho consumida pelo Flask.
    const upsertResult = await pool.query(`
      INSERT INTO site_conteudo_home (
        locale,
        hero_titulo, hero_subtitulo, hero_imagem_url, hero_texto_botao,
        carrosseis, depoimentos,
        estatisticas_clientes, estatisticas_pecas, estatisticas_anos,
        updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        hero_titulo = EXCLUDED.hero_titulo,
        hero_subtitulo = EXCLUDED.hero_subtitulo,
        hero_imagem_url = EXCLUDED.hero_imagem_url,
        hero_texto_botao = EXCLUDED.hero_texto_botao,
        carrosseis = EXCLUDED.carrosseis,
        depoimentos = EXCLUDED.depoimentos,
        estatisticas_clientes = EXCLUDED.estatisticas_clientes,
        estatisticas_pecas = EXCLUDED.estatisticas_pecas,
        estatisticas_anos = EXCLUDED.estatisticas_anos,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.hero_titulo || null,
      data.hero_subtitulo || null,
      hero_imagem_url,
      data.hero_texto_botao || 'Comprar Agora',
      carrosseis,
      depoimentos,
      data.estatisticas_clientes || 5000,
      data.estatisticas_pecas || 10000,
      data.estatisticas_anos || 5
    ]);

    strapi.log.info(`[SYNC] Conteudo Home sincronizado em site_conteudo_home (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    const valores = data.valores ? JSON.stringify(data.valores) : '[]';
    const redes_sociais = data.redes_sociais ? JSON.stringify(data.redes_sociais) : '{}';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_informacoes_empresa (
        locale,
        email, telefone, whatsapp, horario_atendimento,
        valores, redes_sociais,
        updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        email = EXCLUDED.email,
        telefone = EXCLUDED.telefone,
        whatsapp = EXCLUDED.whatsapp,
        horario_atendimento = EXCLUDED.horario_atendimento,
        valores = EXCLUDED.valores,
        redes_sociais = EXCLUDED.redes_sociais,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.email || null,
      data.telefone || null,
      data.whatsapp || null,
      data.horario_atendimento || null,
      valores,
      redes_sociais
    ]);

    strapi.log.info(`[SYNC] Informações Empresa sincronizadas em site_informacoes_empresa (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    // Converter richtext para texto simples se necessário
    const historia_conteudo = typeof data.historia_conteudo === 'string' 
      ? data.historia_conteudo 
      : (data.historia_conteudo?.text || null);
    
    const valores_conteudo = data.valores_conteudo ? JSON.stringify(data.valores_conteudo) : '[]';
    // Strapi v5 schema usa atributo "equipe" (json). No Postgres mantemos compat:
    // - equipe_conteudo (preferencial, usado pelo Flask)
    const equipe_conteudo = data.equipe ? JSON.stringify(data.equipe) : '[]';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_conteudo_sobre (
        locale,
        historia_titulo, historia_conteudo, valores_titulo, valores_conteudo,
        equipe_titulo, equipe_conteudo,
        updated_at
      ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        historia_titulo = EXCLUDED.historia_titulo,
        historia_conteudo = EXCLUDED.historia_conteudo,
        valores_titulo = EXCLUDED.valores_titulo,
        valores_conteudo = EXCLUDED.valores_conteudo,
        equipe_titulo = EXCLUDED.equipe_titulo,
        equipe_conteudo = EXCLUDED.equipe_conteudo,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.historia_titulo || 'Nossa História',
      historia_conteudo,
      data.valores_titulo || 'Nossos Valores',
      valores_conteudo,
      data.equipe_titulo || 'Nossa Equipe',
      equipe_conteudo
    ]);

    strapi.log.info(`[SYNC] Conteudo Sobre sincronizado em site_conteudo_sobre (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    const texto_principal = typeof data.texto_principal === 'string'
      ? data.texto_principal
      : (data.texto_principal?.text || null);
    
    const informacoes = data.informacoes_contato ? JSON.stringify(data.informacoes_contato) : '[]';
    const links = data.redes_sociais ? JSON.stringify(data.redes_sociais) : '{}';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_conteudo_contato (
        locale,
        titulo, texto_principal, informacoes_contato, redes_sociais,
        form_titulo, form_texto,
        updated_at
      ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        texto_principal = EXCLUDED.texto_principal,
        informacoes_contato = EXCLUDED.informacoes_contato,
        redes_sociais = EXCLUDED.redes_sociais,
        form_titulo = EXCLUDED.form_titulo,
        form_texto = EXCLUDED.form_texto,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.titulo || 'Entre em Contato',
      texto_principal,
      informacoes,
      links,
      data.form_titulo || null,
      data.form_texto || null
    ]);

    strapi.log.info(`[SYNC] Conteudo Contato sincronizado em site_conteudo_contato (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_politica_privacidade (
        locale,
        titulo, ultima_atualizacao, conteudo, secoes,
        updated_at
      ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        ultima_atualizacao = EXCLUDED.ultima_atualizacao,
        conteudo = EXCLUDED.conteudo,
        secoes = EXCLUDED.secoes,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.titulo || 'Política de Privacidade',
      data.ultima_atualizacao || null,
      conteudo,
      secoes
    ]);

    strapi.log.info(`[SYNC] Política de Privacidade sincronizada em site_politica_privacidade (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_politica_envio (
        locale,
        titulo, ultima_atualizacao, conteudo, secoes,
        updated_at
      ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        ultima_atualizacao = EXCLUDED.ultima_atualizacao,
        conteudo = EXCLUDED.conteudo,
        secoes = EXCLUDED.secoes,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.titulo || 'Política de Envio',
      data.ultima_atualizacao || null,
      conteudo,
      secoes
    ]);

    strapi.log.info(`[SYNC] Política de Envio sincronizada em site_politica_envio (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
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
    const locale = (data && typeof data.locale === 'string') ? data.locale : '';
    
    const conteudo = typeof data.conteudo === 'string'
      ? data.conteudo
      : (data.conteudo?.text || null);
    
    const secoes = data.secoes ? JSON.stringify(data.secoes) : '[]';
    
    const upsertResult = await pool.query(`
      INSERT INTO site_direitos_reservados (
        locale,
        titulo, ultima_atualizacao, conteudo, secoes,
        updated_at
      ) VALUES ($1, $2, $3, $4::jsonb, $5, NOW())
      ON CONFLICT (locale) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        ultima_atualizacao = EXCLUDED.ultima_atualizacao,
        conteudo = EXCLUDED.conteudo,
        secoes = EXCLUDED.secoes,
        updated_at = NOW()
      RETURNING locale
    `, [
      locale,
      data.titulo || 'Todos os Direitos Reservados',
      data.ultima_atualizacao || null,
      conteudo,
      secoes
    ]);

    strapi.log.info(`[SYNC] Direitos Reservados sincronizado em site_direitos_reservados (locale: ${upsertResult.rows[0]?.locale ?? locale})`);
  } catch (error) {
    strapi.log.error('[SYNC] Erro ao sincronizar Direitos Reservados:', error);
    throw error;
  }
};
