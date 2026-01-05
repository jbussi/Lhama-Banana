/**
 * Sistema de Mensagens Inline
 * Substitui alert() por mensagens visuais no próprio site
 */

class MessageHelper {
    /**
     * Mostra uma mensagem de sucesso
     * @param {string} message - Mensagem a ser exibida
     * @param {HTMLElement} container - Container onde a mensagem será inserida (opcional)
     * @param {number} duration - Duração em ms antes de remover (0 = não remove)
     */
    static showSuccess(message, container = null, duration = 5000) {
        return this.showMessage(message, 'success', container, duration);
    }

    /**
     * Mostra uma mensagem de erro
     * @param {string} message - Mensagem a ser exibida
     * @param {HTMLElement} container - Container onde a mensagem será inserida (opcional)
     * @param {number} duration - Duração em ms antes de remover (0 = não remove)
     */
    static showError(message, container = null, duration = 0) {
        return this.showMessage(message, 'error', container, duration);
    }

    /**
     * Mostra uma mensagem de informação
     * @param {string} message - Mensagem a ser exibida
     * @param {HTMLElement} container - Container onde a mensagem será inserida (opcional)
     * @param {number} duration - Duração em ms antes de remover (0 = não remove)
     */
    static showInfo(message, container = null, duration = 5000) {
        return this.showMessage(message, 'info', container, duration);
    }

    /**
     * Mostra uma mensagem de aviso
     * @param {string} message - Mensagem a ser exibida
     * @param {HTMLElement} container - Container onde a mensagem será inserida (opcional)
     * @param {number} duration - Duração em ms antes de remover (0 = não remove)
     */
    static showWarning(message, container = null, duration = 5000) {
        return this.showMessage(message, 'warning', container, duration);
    }

    /**
     * Cria e exibe uma mensagem inline
     * @param {string} message - Mensagem a ser exibida
     * @param {string} type - Tipo: 'success', 'error', 'info', 'warning'
     * @param {HTMLElement} container - Container onde a mensagem será inserida
     * @param {number} duration - Duração em ms antes de remover (0 = não remove)
     */
    static showMessage(message, type = 'info', container = null, duration = 5000) {
        // Remove mensagens anteriores do mesmo tipo no container
        if (container) {
            const existing = container.querySelector(`.inline-message.${type}`);
            if (existing) {
                existing.remove();
            }
        }

        // Cria elemento da mensagem
        const messageEl = document.createElement('div');
        messageEl.className = `inline-message inline-message-${type}`;
        
        // Ícones por tipo
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };

        messageEl.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button class="inline-message-close" aria-label="Fechar">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Adiciona evento de fechar
        const closeBtn = messageEl.querySelector('.inline-message-close');
        closeBtn.addEventListener('click', () => {
            messageEl.remove();
        });

        // Insere a mensagem
        if (container) {
            // Insere no início do container
            container.insertBefore(messageEl, container.firstChild);
        } else {
            // Insere no topo da página
            const body = document.body;
            if (!body.querySelector('.messages-container')) {
                const messagesContainer = document.createElement('div');
                messagesContainer.className = 'messages-container';
                body.insertBefore(messagesContainer, body.firstChild);
            }
            const messagesContainer = body.querySelector('.messages-container');
            messagesContainer.appendChild(messageEl);
        }

        // Animação de entrada
        setTimeout(() => {
            messageEl.classList.add('show');
        }, 10);

        // Remove automaticamente após duration
        if (duration > 0) {
            setTimeout(() => {
                messageEl.classList.remove('show');
                setTimeout(() => {
                    messageEl.remove();
                }, 300);
            }, duration);
        }

        return messageEl;
    }

    /**
     * Remove todas as mensagens de um container
     * @param {HTMLElement} container - Container (opcional, remove de todos se não especificado)
     */
    static clearMessages(container = null) {
        const selector = container 
            ? container.querySelectorAll('.inline-message')
            : document.querySelectorAll('.inline-message');
        
        selector.forEach(msg => {
            msg.classList.remove('show');
            setTimeout(() => msg.remove(), 300);
        });
    }
}

// Exporta para uso global
window.MessageHelper = MessageHelper;

