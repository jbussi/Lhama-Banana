/**
 * Helper para gerenciar indicadores de carregamento
 */

class LoadingHelper {
    /**
     * Mostra/esconde o page loader
     */
    static showPageLoader() {
        let loader = document.getElementById('page-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'page-loader';
            loader.className = 'page-loader';
            loader.innerHTML = `
                <div class="page-loader-content">
                    <img src="/static/img/logo.png" alt="LhamaBanana" class="page-loader-logo" onerror="this.style.display='none'">
                    <div class="page-loader-spinner"><i class="fas fa-spinner"></i></div>
                    <div class="page-loader-text">Carregando...</div>
                </div>
            `;
            document.body.appendChild(loader);
        }
        loader.classList.remove('hidden');
        loader.style.display = 'flex';
    }

    static hidePageLoader() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.add('hidden');
            setTimeout(() => {
                if (loader.parentNode) {
                    loader.style.display = 'none';
                }
            }, 500);
        }
    }

    /**
     * Adiciona spinner a um botão e o desabilita
     * @param {HTMLElement} button - Botão a ser modificado
     * @param {string} loadingText - Texto a mostrar durante carregamento (opcional)
     * @returns {Object} - { originalHTML, originalDisabled } para restaurar depois
     */
    static setButtonLoading(button, loadingText = null) {
        if (!button) return null;

        const originalHTML = button.innerHTML;
        const originalDisabled = button.disabled;
        const originalText = button.textContent.trim();

        button.disabled = true;
        button.innerHTML = loadingText 
            ? `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`
            : `<i class="fas fa-spinner fa-spin"></i> ${originalText}`;
        
        button.classList.add('loading');

        return { originalHTML, originalDisabled };
    }

    /**
     * Restaura botão ao estado original
     * @param {HTMLElement} button - Botão a ser restaurado
     * @param {Object} state - Estado retornado por setButtonLoading
     */
    static restoreButton(button, state) {
        if (!button || !state) return;

        button.disabled = state.originalDisabled;
        button.innerHTML = state.originalHTML;
        button.classList.remove('loading');
    }
}

// Exporta para uso global
window.LoadingHelper = LoadingHelper;

