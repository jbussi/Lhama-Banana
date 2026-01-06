/**
 * Page Loader - Garante que o visual esteja carregado antes de mostrar a página
 */

(function() {
    'use strict';

    // Criar elemento de loader
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.id = 'page-loader';
    loader.innerHTML = `
        <div class="page-loader-content">
            <img src="/static/img/logo.png" alt="LhamaBanana" class="page-loader-logo" onerror="this.style.display='none'">
            <div class="page-loader-spinner"><i class="fas fa-spinner"></i></div>
            <div class="page-loader-text">Carregando...</div>
        </div>
    `;

    // Adicionar loader ao body
    document.body.insertBefore(loader, document.body.firstChild);

    // Função para esconder o loader
    function hideLoader() {
        const loaderEl = document.getElementById('page-loader');
        if (loaderEl) {
            loaderEl.classList.add('hidden');
            // Remover após animação
            setTimeout(() => {
                if (loaderEl.parentNode) {
                    loaderEl.parentNode.removeChild(loaderEl);
                }
            }, 500);
        }
    }

    // Esconder loader quando tudo estiver carregado
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Aguardar um pouco para garantir que CSS e imagens estejam carregados
            window.addEventListener('load', function() {
                // Aguardar mais um pouco para garantir que tudo esteja renderizado
                setTimeout(hideLoader, 300);
            });
        });
    } else {
        // DOM já está carregado
        window.addEventListener('load', function() {
            setTimeout(hideLoader, 300);
        });
    }

    // Fallback: esconder após 3 segundos mesmo se load não disparar
    setTimeout(hideLoader, 3000);
})();

