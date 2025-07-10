// Dados de exemplo - em um cenário real, isso viria da API
const userData = {
    fullName: "João Silva",
    email: "joao.silva@exemplo.com",
    cpf: "123.456.789-00",
    birthdate: "1990-05-15",
    phone: "11987654321",
    addresses: []
};

// Função para formatar a data
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Função para formatar o telefone
function formatPhone(phone) {
    if (!phone) return '';
    return `(${phone.substring(0,2)}) ${phone.substring(2,7)}-${phone.substring(7)}`;
}

// Função para carregar os dados do usuário
function loadUserData() {
    // Preenche os campos com os dados do usuário
    document.getElementById('profile-name').textContent = userData.fullName;
    document.getElementById('profile-email').textContent = userData.email;
    document.getElementById('profile-phone').textContent = formatPhone(userData.phone);
    
    // Preenche o formulário de edição
    document.getElementById('edit-fullname').value = userData.fullName || '';
    document.getElementById('edit-email').value = userData.email || '';
    document.getElementById('edit-cpf').value = userData.cpf || '';
    document.getElementById('edit-birthdate').value = userData.birthdate || '';
    document.getElementById('edit-phone').value = userData.phone || '';
    
    // Renderiza os endereços
    renderAddresses();
}

// Função para alternar entre visualização e edição das informações pessoais
function togglePersonalInfoEdit() {
    const viewMode = document.getElementById('personal-info-view');
    const editMode = document.getElementById('personal-info-edit');
    const editButton = document.getElementById('edit-personal-info');
    
    if (viewMode.style.display === 'none') {
        // Sai do modo de edição
        viewMode.style.display = 'block';
        editMode.style.display = 'none';
        editButton.innerHTML = '<i class="fas fa-edit"></i> Editar';
    } else {
        // Entra no modo de edição
        viewMode.style.display = 'none';
        editMode.style.display = 'block';
        editButton.innerHTML = '<i class="fas fa-times"></i> Cancelar';
    }
}

// Função para salvar as alterações das informações pessoais
function savePersonalInfo() {
    // Atualiza os dados do usuário
    userData.fullName = document.getElementById('edit-fullname').value;
    userData.email = document.getElementById('edit-email').value;
    userData.cpf = document.getElementById('edit-cpf').value;
    userData.birthdate = document.getElementById('edit-birthdate').value;
    userData.phone = document.getElementById('edit-phone').value;
    
    // Atualiza a visualização
    document.getElementById('profile-name').textContent = userData.fullName;
    document.getElementById('profile-email').textContent = userData.email;
    document.getElementById('profile-phone').textContent = formatPhone(userData.phone);
    
    document.getElementById('view-fullname').textContent = userData.fullName;
    document.getElementById('view-email').textContent = userData.email;
    document.getElementById('view-cpf').textContent = userData.cpf || 'Não informado';
    document.getElementById('view-birthdate').textContent = formatDate(userData.birthdate) || 'Não informada';
    document.getElementById('view-phone').textContent = userData.phone ? formatPhone(userData.phone) : 'Não informado';
    
    // Volta para o modo de visualização
    togglePersonalInfoEdit();
    
    // Aqui você poderia fazer uma chamada para a API para salvar as alterações
    console.log('Dados atualizados:', userData);
}

// Função para mostrar/ocultar o formulário de novo endereço
function toggleNewAddressForm() {
    const form = document.getElementById('new-address-form');
    const addButton = document.getElementById('add-address-btn');
    const addressesList = document.getElementById('addresses-list');
    
    if (form.style.display === 'block') {
        // Esconde o formulário
        form.style.display = 'none';
        addButton.innerHTML = '<i class="fas fa-plus"></i> Novo Endereço';
        
        // Mostra a lista de endereços (ou mensagem de lista vazia)
        addressesList.style.display = 'block';
    } else {
        // Mostra o formulário
        form.style.display = 'block';
        addButton.innerHTML = '<i class="fas fa-times"></i> Cancelar';
        
        // Esconde a lista de endereços
        addressesList.style.display = 'none';
        
        // Rola a página até o formulário
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

// Função para adicionar um novo endereço
function addNewAddress() {
    const type = document.getElementById('address-type').value;
    const name = document.getElementById('address-name').value;
    const zipcode = document.getElementById('address-zipcode').value;
    const street = document.getElementById('address-street').value;
    const number = document.getElementById('address-number').value;
    const complement = document.getElementById('address-complement').value;
    const neighborhood = document.getElementById('address-neighborhood').value;
    const city = document.getElementById('address-city').value;
    const state = document.getElementById('address-state').value;
    const reference = document.getElementById('address-reference').value;
    
    // Validação básica
    if (!street || !number || !neighborhood || !city || !state) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }
    
    // Cria o novo endereço
    const newAddress = {
        id: Date.now(), // ID único baseado no timestamp
        type: type,
        name: name,
        zipcode: zipcode,
        street: street,
        number: number,
        complement: complement,
        neighborhood: neighborhood,
        city: city,
        state: state,
        reference: reference,
        isDefault: userData.addresses.length === 0 // Primeiro endereço é definido como padrão
    };
    
    // Adiciona o endereço à lista
    userData.addresses.push(newAddress);
    
    // Reseta o formulário
    document.getElementById('new-address-form').reset();
    
    // Atualiza a exibição
    renderAddresses();
    
    // Volta para a visualização da lista
    toggleNewAddressForm();
    
    console.log('Novo endereço adicionado:', newAddress);
}

// Função para renderizar a lista de endereços
function renderAddresses() {
    const container = document.getElementById('addresses-list');
    
    if (userData.addresses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-map-marked-alt"></i>
                <h3>Nenhum endereço cadastrado</h3>
                <p>Adicione um endereço para facilitar suas compras.</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="addresses-grid">';
    
    userData.addresses.forEach(address => {
        const typeText = {
            'home': 'Casa',
            'work': 'Trabalho',
            'other': 'Outro'
        }[address.type] || 'Endereço';
        
        html += `
            <div class="address-card ${address.isDefault ? 'default' : ''}" data-id="${address.id}">
                <div class="address-header">
                    <h4>${address.name || typeText}</h4>
                    ${address.isDefault ? '<span class="default-badge">Padrão</span>' : ''}
                </div>
                <div class="address-details">
                    <p>${address.street}, ${address.number}${address.complement ? ', ' + address.complement : ''}</p>
                    <p>${address.neighborhood} - ${address.city}/${address.state}</p>
                    <p>CEP: ${address.zipcode || 'Não informado'}</p>
                    ${address.reference ? `<p class="reference"><strong>Referência:</strong> ${address.reference}</p>` : ''}
                </div>
                <div class="address-actions">
                    <button class="btn btn-outline btn-sm set-default" ${address.isDefault ? 'disabled' : ''}>
                        <i class="fas fa-star"></i> Tornar padrão
                    </button>
                    <button class="btn btn-outline btn-sm edit-address">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-outline btn-sm delete-address">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    // Configura os botões de ação
    setupAddressButtons();
}

// Função para configurar os botões de ação dos endereços
function setupAddressButtons() {
    // Botão de definir como padrão
    document.querySelectorAll('.set-default').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.address-card');
            const addressId = parseInt(card.dataset.id);
            
            // Atualiza todos os endereços
            userData.addresses.forEach(addr => {
                addr.isDefault = (addr.id === addressId);
            });
            
            // Re-renderiza a lista
            renderAddresses();
            
            console.log('Endereço padrão alterado:', addressId);
        });
    });
    
    // Botão de editar endereço
    document.querySelectorAll('.edit-address').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.address-card');
            const addressId = parseInt(card.dataset.id);
            const address = userData.addresses.find(addr => addr.id === addressId);
            
            if (!address) return;
            
            // Preenche o formulário com os dados do endereço
            document.getElementById('address-type').value = address.type;
            document.getElementById('address-name').value = address.name || '';
            document.getElementById('address-zipcode').value = address.zipcode || '';
            document.getElementById('address-street').value = address.street || '';
            document.getElementById('address-number').value = address.number || '';
            document.getElementById('address-complement').value = address.complement || '';
            document.getElementById('address-neighborhood').value = address.neighborhood || '';
            document.getElementById('address-city').value = address.city || '';
            document.getElementById('address-state').value = address.state || '';
            document.getElementById('address-reference').value = address.reference || '';
            
            // Remove o endereço da lista
            userData.addresses = userData.addresses.filter(addr => addr.id !== addressId);
            
            // Atualiza a exibição
            renderAddresses();
            
            // Mostra o formulário
            toggleNewAddressForm();
        });
    });
    
    // Botão de excluir endereço
    document.querySelectorAll('.delete-address').forEach(button => {
        button.addEventListener('click', function() {
            if (!confirm('Tem certeza que deseja excluir este endereço?')) {
                return;
            }
            
            const card = this.closest('.address-card');
            const addressId = parseInt(card.dataset.id);
            
            // Remove o endereço da lista
            userData.addresses = userData.addresses.filter(addr => addr.id !== addressId);
            
            // Se o endereço excluído era o padrão e ainda houver endereços, define o primeiro como padrão
            if (userData.addresses.length > 0 && !userData.addresses.some(addr => addr.isDefault)) {
                userData.addresses[0].isDefault = true;
            }
            
            // Atualiza a exibição
            renderAddresses();
            
            console.log('Endereço excluído:', addressId);
        });
    });
}

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Carrega os dados do usuário
    loadUserData();
    
    // Configura os botões de informações pessoais
    document.getElementById('edit-personal-info').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('cancel-personal-edit').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('save-personal-info').addEventListener('click', savePersonalInfo);
    
    // Configura os botões de endereços
    document.getElementById('add-address-btn').addEventListener('click', toggleNewAddressForm);
    document.getElementById('cancel-new-address').addEventListener('click', toggleNewAddressForm);
    document.getElementById('save-new-address').addEventListener('click', addNewAddress);
    
    // Configura o botão de trocar foto de perfil
    document.getElementById('change-avatar-btn').addEventListener('click', function() {
        document.getElementById('profile-pic-input').click();
    });
    
    // Configura o input de upload de foto
    document.getElementById('profile-pic-input').addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(event) {
                document.getElementById('profile-pic').src = event.target.result;
                // Aqui você poderia enviar a imagem para o servidor
            };
            
            reader.readAsDataURL(e.target.files[0]);
        }
    });
});
