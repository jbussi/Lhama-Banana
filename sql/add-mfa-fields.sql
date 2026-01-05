-- Adicionar campos para Multi-Factor Authentication (2FA)
-- Apenas para administradores

-- Adicionar campo para armazenar o secret do TOTP
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(32);

-- Adicionar campo para indicar se 2FA está habilitado
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE;

-- Criar índice para otimizar consultas
CREATE INDEX IF NOT EXISTS idx_usuarios_mfa_enabled ON usuarios (mfa_enabled) WHERE mfa_enabled = TRUE;

-- Comentário
COMMENT ON COLUMN usuarios.mfa_secret IS 'Secret key para geração de códigos TOTP (2FA)';
COMMENT ON COLUMN usuarios.mfa_enabled IS 'Indica se a verificação em duas etapas está habilitada para este usuário';


