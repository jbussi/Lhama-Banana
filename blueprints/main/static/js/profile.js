// Importações Firebase: essencial para usar os serviços de autenticação e inicializar o app
// AJUSTE OS URLs ABAIXO CONFORME SUA CONFIGURAÇÃO DE CDN OU IMPORTMAP!
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

// Sua configuração do Firebase: ESSA DEVE SER A MESMA EM TODOS OS SEUS ARQUIVOS JS DE FRONTEND!
const firebaseConfig = {
  apiKey: "AIzaSyDd13Tl9dJaUqIvNhGWakoEbpYqw7ZrB7Y",
  authDomain: "lhamabanana-981d5.firebaseapp.com",
  projectId: "lhamabanana-981d5",
  storageBucket: "lhamabanana-981d5.firebasestorage.app",
  messagingSenderId: "209130422039",
  appId: "1:209130422039:web:70fcf2089fa90715364152",
  measurementId: "G-4XQSZZB0JK"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app); // Instância do Firebase Auth para gerenciar a autenticação

// Variável global para armazenar os dados do usuário.
// Inicializamos com 'addresses' vazio para garantir que a propriedade existe.
let usuario = { addresses: [] }; 

// --- Funções Auxiliares de Formatação ---

// Formata a data para exibição.
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);

    // CORREÇÃO: Adiciona 1 dia para compensar o fuso horário se a data
    // for interpretada como UTC meia-noite e seu fuso horário for negativo.
    // Isso é mais comum para datas sem componente de tempo (YYYY-MM-DD).
    date.setDate(date.getDate() + 1); 
    
    return date.toLocaleDateString('pt-BR');
}

// Formata o telefone para exibição (ex: (XX) XXXXX-XXXX).
function formatPhone(phone) {
    if (!phone) return '';
    const cleaned = ('' + phone).replace(/\D/g, ''); // Remove tudo que não for dígito
    const match5 = cleaned.match(/^(\d{2})(\d{5})(\d{4})$/); // (XX) 9XXXX-XXXX
    if (match5) {
      return `(${match5[1]}) ${match5[2]}-${match5[3]}`;
    }
    const match4 = cleaned.match(/^(\d{2})(\d{4})(\d{4})$/); // (XX) XXXX-XXXX
    if (match4) {
      return `(${match4[1]}) ${match4[2]}-${match4[3]}`;
    }
    return phone; // Retorna como está se não corresponder aos padrões
}

// --- Funções de Carregamento e Atualização da UI ---

// Carrega os dados recebidos do backend na variável global 'usuario' e atualiza a interface.
function loadUserData(data) {
    console.log("Dados recebidos para loadUserData:", data); // Para depuração
    usuario = data; // Popula a variável global 'usuario' com os dados recebidos

    // Garante que 'addresses' seja um array, mesmo que vazio ou não vindo do backend ainda.
    if (!usuario.addresses) {
        usuario.addresses = [];
    }
    
    // Preenche os campos de visualização de perfil no cabeçalho
    document.getElementById('profile-name').textContent = usuario.nome || 'Usuário'; 
    document.getElementById('profile-join-date').textContent = formatDate(usuario.criado_em) || 'Não informado'; // Assegure que 'criado_em' vem do backend
    
    // Preenche os campos de visualização na seção "Informações Pessoais"
    document.getElementById('view-name').textContent = usuario.nome || 'Não informado'; // 'view-name' no HTML
    document.getElementById('view-email').textContent = usuario.email || 'Não informado';
    document.getElementById('view-cpf').textContent = usuario.cpf || 'Não informado';
    document.getElementById('view-birthdate').textContent = formatDate(usuario.data_nascimento) || 'Não informada';
    document.getElementById('view-phone').textContent = formatPhone(usuario.telefone) || 'Não informado';

    // Preenche os campos do formulário de edição
    document.getElementById('edit-name').value = usuario.nome || ''; // CORRIGIDO: 'edit-name' para o HTML
    document.getElementById('edit-email').value = usuario.email || '';
    document.getElementById('edit-cpf').value = usuario.cpf || '';
    document.getElementById('edit-birthdate').value = usuario.data_nascimento || ''; // 'YYYY-MM-DD' para input type="date"
    document.getElementById('edit-phone').value = usuario.telefone || '';
    
    // Por enquanto, renderAddresses usa os dados locais de 'usuario.addresses'.
    renderAddresses(); 
}

// --- Funções de UI (edição de informações pessoais) ---

// Alterna a visibilidade entre o modo de visualização e o formulário de edição.
function togglePersonalInfoEdit() {
    const viewMode = document.getElementById('personal-info-view');
    const editMode = document.getElementById('personal-info-edit');
    const editButton = document.getElementById('edit-btn'); 

    if (viewMode.style.display === 'none') {
        // Sai do modo de edição para visualização
        viewMode.style.display = 'grid'; // Ajuste 'grid' ou 'block' conforme seu CSS
        editMode.style.display = 'none';
        editButton.innerHTML = '<i class="fas fa-edit"></i> Editar'; 
    } else {
        // Entra no modo de edição
        viewMode.style.display = 'none';
        editMode.style.display = 'grid'; // Ajuste 'grid' ou 'block' conforme seu CSS
        editButton.innerHTML = '<i class="fas fa-times"></i> Cancelar'; 
    }
}

// Salva as alterações das informações pessoais fazendo uma chamada PUT para o backend.
async function savePersonalInfo() {
    // Coleta os dados do formulário de edição
    const dataToSave = {
        nome: document.getElementById('edit-name').value, // CORRIGIDO: 'edit-name' para o HTML
        email: document.getElementById('edit-email').value,
        cpf: document.getElementById('edit-cpf').value,
        data_nascimento: document.getElementById('edit-birthdate').value,
        telefone: document.getElementById('edit-phone').value
    };

    try {
        const currentUser = auth.currentUser;
        if (!currentUser) {
            alert('Você precisa estar logado para atualizar o perfil.');
            window.location.href = '/login_page'; 
            return;
        }
        const idToken = await currentUser.getIdToken(); // Obtém o ID Token JWT do Firebase

        const response = await fetch("http://localhost:80/api/user_data", {
            method: "PUT", // Usamos PUT para indicar uma atualização de recurso existente
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${idToken}` // Envia o token para autenticação no backend
            },
            body: JSON.stringify(dataToSave)
        });

        if (!response.ok) {
            const errorData = await response.json(); // Tenta ler o JSON de erro do backend.
            throw new Error(errorData.erro || "Erro desconhecido ao salvar o perfil.");
        }

        const successData = await response.json(); 
        console.log("Dados do perfil salvos com sucesso:", successData.mensagem);
        alert("Perfil atualizado com sucesso!");

        // Atualiza a variável 'usuario' localmente com os dados que foram salvos.
        Object.assign(usuario, dataToSave); 
        
        // Recarrega os dados na UI a partir da variável 'usuario' atualizada.
        loadUserData(usuario); 

        // Volta para o modo de visualização.
        togglePersonalInfoEdit();

    } catch (error) {
        console.error("Erro ao salvar informações pessoais:", error);
        alert("Erro ao salvar informações: " + error.message);
    }
}

// --- Funções de UI (endereços) ---
// Estas funções ainda estão operando APENAS no frontend.
// A persistência no backend (tabela de endereços, APIs CRUD) será implementada depois.

function toggleNewAddressForm() {
    const form = document.getElementById('new-address-form');
    const addButton = document.getElementById('add-address-btn');
    const addressesList = document.getElementById('addresses-list');
    
    if (form.style.display === 'block') {
        form.style.display = 'none';
        addButton.innerHTML = '<i class="fas fa-plus"></i> Novo Endereço';
        addressesList.style.display = 'grid'; // Ajuste conforme seu CSS
    } else {
        form.style.display = 'grid'; // Ajuste conforme seu CSS
        addButton.innerHTML = '<i class="fas fa-times"></i> Cancelar';
        addressesList.style.display = 'none';
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

function addNewAddress() {
    const type = document.getElementById('address-type').value;
    const name = document.getElementById('address-name').value;
    const zipcode = document.getElementById('address-zipcode').value; // CORRIGIDO: 'address-zipcode'
    const street = document.getElementById('address-street').value;
    const number = document.getElementById('address-number').value;
    const complement = document.getElementById('address-complement').value;
    const neighborhood = document.getElementById('address-neighborhood').value;
    const city = document.getElementById('address-city').value;
    const state = document.getElementById('address-state').value;
    const reference = document.getElementById('address-reference').value;
    
    // Validação básica (pode ser expandida)
    if (!street || !number || !neighborhood || !city || !state || !zipcode) {
        alert('Por favor, preencha todos os campos obrigatórios do endereço (rua, número, bairro, cidade, estado, CEP).');
        return;
    }
    
    const newAddress = {
        id: Date.now(), // ID temporário, para controle no frontend
        type: type, name: name, zipcode: zipcode, street: street,
        number: number, complement: complement, neighborhood: neighborhood,
        city: city, state: state, reference: reference,
        isDefault: usuario.addresses.length === 0 // Define como padrão se for o primeiro
    };
    
    usuario.addresses.push(newAddress); // CORRIGIDO: usa 'usuario.addresses'
    document.getElementById('new-address-form').reset(); // Limpa o formulário
    renderAddresses(); // Re-renderiza a lista para atualizar a UI
    toggleNewAddressForm(); // Esconde o formulário
    console.log('Novo endereço adicionado (localmente):', newAddress);
    // FUTURO: Aqui você fará uma chamada POST para o seu backend para salvar o endereço de forma persistente.
}

function renderAddresses() {
    const container = document.getElementById('addresses-list');
    
    if (usuario.addresses.length === 0) { // CORRIGIDO: usa 'usuario.addresses'
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
    usuario.addresses.forEach(address => { // CORRIGIDO: usa 'usuario.addresses'
        const typeText = { 'home': 'Casa', 'work': 'Trabalho', 'other': 'Outro' }[address.type] || 'Endereço';
        
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
                    <button class="btn btn-outline btn-sm set-default" ${address.isDefault ? 'disabled' : ''} data-id="${address.id}">
                        <i class="fas fa-star"></i> Tornar padrão
                    </button>
                    <button class="btn btn-outline btn-sm edit-address" data-id="${address.id}">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-outline btn-sm delete-address" data-id="${address.id}">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
    
    // Configura os event listeners para os botões dos endereços recém-renderizados.
    setupAddressButtons(); 
}

function setupAddressButtons() {
    // Adiciona listener para o botão "Tornar padrão"
    document.querySelectorAll('.set-default').forEach(button => {
        button.addEventListener('click', function() {
            const addressId = parseInt(this.dataset.id); 
            usuario.addresses.forEach(addr => { // CORRIGIDO: usa 'usuario.addresses'
                addr.isDefault = (addr.id === addressId); 
            });
            renderAddresses(); // Re-renderiza para atualizar a UI
            console.log('Endereço padrão alterado (localmente):', addressId);
            // FUTURO: Chamar API PUT para atualizar o padrão no backend
        });
    });
    
    // Adiciona listener para o botão "Editar" endereço
    document.querySelectorAll('.edit-address').forEach(button => {
        button.addEventListener('click', function() {
            const addressId = parseInt(this.dataset.id);
            const address = usuario.addresses.find(addr => addr.id === addressId); // CORRIGIDO: usa 'usuario.addresses'
            if (!address) return;
            
            // Preenche o formulário com os dados do endereço para edição
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
            
            // Remove o endereço da lista local (ele será recriado/atualizado ao salvar)
            usuario.addresses = usuario.addresses.filter(addr => addr.id !== addressId); // CORRIGIDO: usa 'usuario.addresses'
            renderAddresses(); // Re-renderiza sem o endereço editado
            toggleNewAddressForm(); // Mostra o formulário para edição
            console.log('Editando endereço (localmente):', addressId);
            // FUTURO: Chamar API PUT para atualizar o endereço no backend
        });
    });
    
    // Adiciona listener para o botão "Excluir" endereço
    document.querySelectorAll('.delete-address').forEach(button => {
        button.addEventListener('click', function() {
            if (!confirm('Tem certeza que deseja excluir este endereço?')) return;
            
            const addressId = parseInt(this.dataset.id);
            usuario.addresses = usuario.addresses.filter(addr => addr.id !== addressId); // CORRIGIDO: usa 'usuario.addresses'
            
            // Se o endereço excluído era o padrão e ainda há endereços, define o primeiro como padrão
            if (usuario.addresses.length > 0 && !usuario.addresses.some(addr => addr.isDefault)) { // CORRIGIDO: usa 'usuario.addresses'
                usuario.addresses[0].isDefault = true; // CORRIGIDO: usa 'usuario.addresses'
            }
            renderAddresses(); // Re-renderiza
            console.log('Endereço excluído (localmente):', addressId);
            // FUTURO: Chamar API DELETE para excluir o endereço no backend
        });
    });
}

// --- Inicialização do script quando o DOM estiver carregado ---

document.addEventListener('DOMContentLoaded', function() {
    // Escuta mudanças no estado de autenticação do Firebase.
    // Isso é CRÍTICO para garantir que temos um usuário logado e seu ID Token
    // antes de tentar carregar os dados do backend.
    onAuthStateChanged(auth, async (user) => {
        if (user) {
            // Usuário logado no Firebase, agora podemos tentar carregar os dados do backend
            try {
                const idToken = await user.getIdToken(); // Obtém o ID Token JWT do Firebase

                const response = await fetch("http://localhost:80/api/user_data", {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${idToken}` // Envia o token para autenticação no backend
                    }
                });

                if (!response.ok) {
                    // Trata respostas HTTP que não são sucesso (ex: 401, 404, 500)
                    if (response.status === 401) {
                        alert("Sessão expirada ou não autorizada. Por favor, faça login novamente.");
                        window.location.href = '/auth.login_page'; // Redireciona para a página de login do Flask
                    } else {
                        const errorData = await response.json(); // Tenta ler o JSON de erro do backend
                        throw new Error(errorData.erro || "Erro desconhecido ao carregar dados do perfil.");
                    }
                }

                const data = await response.json(); // Parseia a resposta JSON
                console.log("Dados do perfil carregados do backend:", data);
                loadUserData(data); // Carrega os dados recebidos e atualiza a UI

            } catch (error) {
                console.error("Erro ao carregar o perfil:", error);
                alert("Ocorreu um erro ao carregar seu perfil. Por favor, tente novamente mais tarde.");
                // Opcional: Redirecionar ou deslogar o usuário em caso de erro grave.
            }
        } else {
            // Usuário não logado no Firebase, redireciona para a página de login.
            alert('Você precisa estar logado para acessar esta página.');
            window.location.href = '/auth.login_page'; 
        }
    });

    // --- Configuração dos Listeners de Evento para os botões ---
    // Estes listeners são configurados uma única vez, após o DOM estar pronto.

    // Botões de informações pessoais
    // CORRIGIDO: Usando os IDs corretos do HTML, e removendo as declarações duplicadas.
    document.getElementById('edit-btn').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('cancel-btn').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('save-btn').addEventListener('click', savePersonalInfo);

    // Botões de endereços
    document.getElementById('add-address-btn').addEventListener('click', toggleNewAddressForm);
    document.getElementById('cancel-new-address').addEventListener('click', toggleNewAddressForm);
    document.getElementById('save-new-address').addEventListener('click', addNewAddress);
    
    // Botão de trocar foto de perfil (ainda com lógica local)
    document.getElementById('change-avatar-btn').addEventListener('click', function() {
        document.getElementById('profile-pic-input').click();
    });
    
    document.getElementById('profile-pic-input').addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            reader.onload = function(event) {
                document.getElementById('profile-pic').src = event.target.result;
                // FUTURO: Aqui você enviaria a imagem para o Cloud Storage for Firebase.
            };
            reader.readAsDataURL(e.target.files[0]);
        }
    });
});
