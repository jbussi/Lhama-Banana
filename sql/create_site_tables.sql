-- Tabelas "espelho" para o frontend (Flask) ler, sem conflitar com as tabelas internas do Strapi.
-- A ideia é: Strapi salva nas tabelas dele (ex.: conteudo_contato), e os lifecycles sincronizam para site_*.
-- Assim evitamos duplicação/loops e o bug "salva e volta para valor anterior".

CREATE TABLE IF NOT EXISTS site_conteudo_contato (
  locale TEXT NOT NULL DEFAULT '',
  titulo TEXT,
  texto_principal TEXT,
  informacoes_contato JSONB NOT NULL DEFAULT '[]'::jsonb,
  redes_sociais JSONB NOT NULL DEFAULT '{}'::jsonb,
  form_titulo TEXT,
  form_texto TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

CREATE TABLE IF NOT EXISTS site_conteudo_home (
  locale TEXT NOT NULL DEFAULT '',
  hero_titulo TEXT,
  hero_subtitulo TEXT,
  hero_imagem_url TEXT,
  hero_texto_botao TEXT,
  carrosseis JSONB NOT NULL DEFAULT '[]'::jsonb,
  depoimentos JSONB NOT NULL DEFAULT '[]'::jsonb,
  estatisticas_clientes INTEGER,
  estatisticas_pecas INTEGER,
  estatisticas_anos INTEGER,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

CREATE TABLE IF NOT EXISTS site_informacoes_empresa (
  locale TEXT NOT NULL DEFAULT '',
  email TEXT,
  telefone TEXT,
  whatsapp TEXT,
  horario_atendimento TEXT,
  valores JSONB NOT NULL DEFAULT '[]'::jsonb,
  redes_sociais JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

CREATE TABLE IF NOT EXISTS site_politica_privacidade (
  locale TEXT NOT NULL DEFAULT '',
  titulo TEXT,
  ultima_atualizacao DATE,
  conteudo TEXT,
  secoes JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

CREATE TABLE IF NOT EXISTS site_politica_envio (
  locale TEXT NOT NULL DEFAULT '',
  titulo TEXT,
  ultima_atualizacao DATE,
  conteudo TEXT,
  secoes JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

CREATE TABLE IF NOT EXISTS site_direitos_reservados (
  locale TEXT NOT NULL DEFAULT '',
  titulo TEXT,
  ultima_atualizacao DATE,
  conteudo TEXT,
  secoes JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (locale)
);

