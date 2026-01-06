# Código de Alinhamento de Ícones (Olhos e Ícones da Esquerda)

## Problema
Os ícones de "olho" (toggle-password) precisam estar perfeitamente alinhados verticalmente com os ícones da esquerda (form-group i) dentro das caixas de input de senha.

## Estrutura HTML

```html
<div class="form-group">
    <label for="password">Senha</label>
    <i class="fas fa-lock"></i>  <!-- Ícone da esquerda -->
    <input type="password" id="password" name="password" placeholder="Digite sua senha" required>
    <span class="toggle-password" id="toggle-password-login">  <!-- Ícone do olho -->
        <i class="fas fa-eye"></i>
    </span>
</div>
```

## CSS Atual

```css
/* Container do formulário */
.form-group {
    margin-bottom: 28px;
    position: relative;
}

/* Label acima do input */
.form-group label {
    display: block;
    margin-bottom: 12px;
    font-weight: 600;
    color: var(--cor-texto-cinza);
    font-size: 0.95rem;
    line-height: 1.2;
    height: auto;
}

/* Input de texto/senha */
.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"],
.form-group input {
    width: 100%;
    padding: 0 45px 0 40px;  /* 45px direita (para o olho), 40px esquerda (para o ícone) */
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    font-size: 0.95rem;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    background-color: #fafafa;
    box-sizing: border-box;
    height: 46px;  /* Altura fixa do input */
    line-height: 1.2;
    margin: 0;
}

/* Ícone da esquerda (cadeado, envelope, usuário) */
.form-group i {
    position: absolute;
    left: 15px;
    top: 54px;  /* Calculado: label margin-bottom (12px) + label altura (~19px) + metade do input (23px) = 54px */
    transform: translateY(-50%);  /* Centraliza verticalmente */
    color: #666;
    transition: color 0.3s ease;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    pointer-events: none;
    z-index: 1;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    border: none !important;
    outline: none !important;
    box-sizing: border-box;
}

/* Container do olho (toggle-password) */
.toggle-password {
    position: absolute;
    right: 15px;
    top: 54px;  /* Mesmo valor do ícone da esquerda */
    transform: translateY(-50%);  /* Mesmo transform do ícone da esquerda */
    cursor: pointer;
    width: 20px;  /* Diferente do ícone da esquerda (16px) */
    height: 20px;  /* Diferente do ícone da esquerda (16px) */
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    z-index: 2;
    transition: color 0.3s ease;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    outline: none !important;
    box-sizing: border-box;
}

/* Ícone dentro do toggle-password */
.toggle-password i {
    font-size: 14px;
    pointer-events: none;
    position: static;
    width: auto;
    height: auto;
    margin: 0 !important;
    padding: 0 !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1 !important;
    vertical-align: middle;
}
```

## Cálculo da Posição

A posição `top: 54px` é calculada assim:
- `label margin-bottom`: 12px
- `label altura aproximada`: ~19px (baseado em font-size 0.95rem e line-height 1.2)
- `metade da altura do input`: 23px (input tem 46px de altura, então 46/2 = 23px)
- **Total**: 12px + 19px + 23px = 54px

O `transform: translateY(-50%)` move o elemento para cima em 50% da sua própria altura, centralizando-o verticalmente no ponto calculado.

## Problema Identificado

O ícone do olho (`toggle-password`) tem `width: 20px` e `height: 20px`, enquanto o ícone da esquerda (`form-group i`) tem `width: 16px` e `height: 16px`. Isso pode causar desalinhamento visual mesmo que ambos estejam na mesma posição `top` e com o mesmo `transform`.

## Objetivo

Garantir que ambos os ícones fiquem perfeitamente alinhados verticalmente no centro do input, independentemente de suas dimensões.


