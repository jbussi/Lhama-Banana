/**
 * Sistema de Notificações - LhamaBanana
 * Notificações modernas e divertidas mantendo o estilo infantil
 */

class NotificationSystem {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.init();
    }

    init() {
        // Criar container se não existir
        if (!document.querySelector('.notifications-container')) {
            this.container = document.createElement('div');
            this.container.className = 'notifications-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.notifications-container');
        }
    }

    /**
     * Mostrar notificação
     * @param {Object} options - Opções da notificação
     * @param {string} options.type - Tipo: 'success', 'error', 'warning', 'info'
     * @param {string} options.title - Título da notificação
     * @param {string} options.message - Mensagem da notificação
     * @param {number} options.duration - Duração em ms (padrão: 5000)
     * @param {Array} options.actions - Ações disponíveis
     * @param {boolean} options.toast - Se é toast (menor)
     */
    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 5000,
            actions = [],
            toast = false
        } = options;

        const id = this.generateId();
        const notification = this.createNotification(id, type, title, message, actions, toast);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // Mostrar com animação
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Auto-remover se tiver duração
        if (duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }

        return id;
    }

    /**
     * Criar elemento da notificação
     */
    createNotification(id, type, title, message, actions, toast) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} ${toast ? 'notification-toast' : ''}`;
        notification.dataset.id = id;

        const icon = this.getIcon(type);
        const progressBar = duration > 0 ? '<div class="notification-progress"></div>' : '';

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icon}</div>
                <div class="notification-text">
                    ${title ? `<div class="notification-title">${title}</div>` : ''}
                    <div class="notification-message">${message}</div>
                    ${actions.length > 0 ? this.createActions(actions) : ''}
                </div>
            </div>
            <button class="notification-close" onclick="notifications.hide('${id}')">×</button>
            ${progressBar}
        `;

        return notification;
    }

    /**
     * Criar ações da notificação
     */
    createActions(actions) {
        const actionsHtml = actions.map(action => 
            `<button class="btn-small ${action.class || 'btn-outline'}" onclick="${action.onclick}">${action.text}</button>`
        ).join('');

        return `<div class="notification-action">${actionsHtml}</div>`;
    }

    /**
     * Obter ícone baseado no tipo
     */
    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    /**
     * Esconder notificação
     */
    hide(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.classList.add('hide');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 400);
        }
    }

    /**
     * Esconder todas as notificações
     */
    hideAll() {
        this.notifications.forEach((notification, id) => {
            this.hide(id);
        });
    }

    /**
     * Gerar ID único
     */
    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Instância global
const notifications = new NotificationSystem();

// Métodos de conveniência
window.showNotification = {
    success: (title, message, options = {}) => 
        notifications.show({ type: 'success', title, message, ...options }),
    
    error: (title, message, options = {}) => 
        notifications.show({ type: 'error', title, message, ...options }),
    
    warning: (title, message, options = {}) => 
        notifications.show({ type: 'warning', title, message, ...options }),
    
    info: (title, message, options = {}) => 
        notifications.show({ type: 'info', title, message, ...options }),
    
    toast: (message, type = 'info', options = {}) => 
        notifications.show({ type, message, toast: true, duration: 3000, ...options })
};

// Exemplos de uso:
/*
// Notificação simples
showNotification.success('Sucesso!', 'Produto adicionado ao carrinho');

// Notificação com ação
showNotification.info('Carrinho', 'Você tem itens no carrinho', {
    actions: [
        { text: 'Ver Carrinho', class: 'btn-primary', onclick: 'window.location.href="/carrinho"' }
    ]
});

// Toast
showNotification.toast('Produto adicionado!', 'success');

// Notificação persistente
showNotification.warning('Atenção', 'Verifique seus dados', { duration: 0 });
*/

