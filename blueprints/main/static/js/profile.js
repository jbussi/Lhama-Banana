// Importações Firebase: essencial para usar os serviços de autenticação e inicializar o app
// AJUSTE OS URLs ABAIXO CONFORME SUA CONFIGURAÇÃO DE CDN OU IMPORTMAP!
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getAuth, onAuthStateChanged, sendEmailVerification, updatePassword, reauthenticateWithCredential, EmailAuthProvider, signOut } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

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
let editingAddressId = null; // ID do endereço sendo editado (null = novo endereço) 

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
    
    // Preservar endereços existentes antes de sobrescrever
    const existingAddresses = usuario.addresses || [];
    
    // Popula a variável global 'usuario' com os dados recebidos, preservando endereços
    usuario = { ...data };
    
    // Se os dados vierem com endereços, usar eles, senão preservar os existentes
    if (data.addresses && Array.isArray(data.addresses) && data.addresses.length > 0) {
        usuario.addresses = data.addresses;
    } else {
        usuario.addresses = existingAddresses;
    }
    
    // Garantir que addresses seja sempre um array
    if (!usuario.addresses || !Array.isArray(usuario.addresses)) {
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
    
    // Renderizar endereços se já existirem
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
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Você precisa estar logado para atualizar o perfil.', messagesContainer);
            } else {
            alert('Você precisa estar logado para atualizar o perfil.');
            }
            window.location.href = '/login_page'; 
            return;
        }
        const idToken = await currentUser.getIdToken(); // Obtém o ID Token JWT do Firebase

        const response = await fetch("/api/user_data", {
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
        const messagesContainer = document.getElementById('profile-messages-container');
        if (messagesContainer && window.MessageHelper) {
            window.MessageHelper.showSuccess("Perfil atualizado com sucesso!", messagesContainer, 3000);
        } else {
        alert("Perfil atualizado com sucesso!");
        }

        // Atualiza a variável 'usuario' localmente com os dados que foram salvos.
        Object.assign(usuario, dataToSave); 
        
        // Recarrega os dados na UI a partir da variável 'usuario' atualizada.
        loadUserData(usuario); 

        // Volta para o modo de visualização.
        togglePersonalInfoEdit();

    } catch (error) {
        console.error("Erro ao salvar informações pessoais:", error);
        const messagesContainer = document.getElementById('profile-messages-container');
        if (messagesContainer && window.MessageHelper) {
            window.MessageHelper.showError("Erro ao salvar informações: " + error.message, messagesContainer);
        } else {
        alert("Erro ao salvar informações: " + error.message);
        }
    }
}

// --- Funções de UI (endereços) ---
// Estas funções ainda estão operando APENAS no frontend.
// A persistência no backend (tabela de endereços, APIs CRUD) será implementada depois.

function toggleNewAddressForm() {
    const form = document.getElementById('new-address-form');
    const addButton = document.getElementById('add-address-btn');
    const addressesList = document.getElementById('addresses-list');
    
    if (form.style.display === 'grid' || form.style.display === 'block') {
        // Fechar formulário
        form.style.display = 'none';
        addButton.innerHTML = '<i class="fas fa-plus"></i> Novo Endereço';
        if (addressesList) addressesList.style.display = 'grid';
        form.reset(); // Limpar formulário
        editingAddressId = null; // Resetar ID de edição
    } else {
        // Abrir formulário
        form.style.display = 'grid';
        addButton.innerHTML = '<i class="fas fa-times"></i> Cancelar';
        if (addressesList) addressesList.style.display = 'none';
        form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        editingAddressId = null; // Novo endereço
    }
}

// Função para buscar endereço por CEP (similar ao checkout)
async function fetchAddressByCEP(cep) {
    try {
        const cleanCEP = cep.replace(/\D/g, '');
        if (cleanCEP.length !== 8) return null;
        const response = await fetch(`https://viacep.com.br/ws/${cleanCEP}/json/`);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const data = await response.json();
        if (data.erro) {
            if (window.MessageHelper) {
                window.MessageHelper.showError('CEP não encontrado. Verifique o CEP digitado.', document.getElementById('new-address-form'));
            } else {
                const messagesContainer = document.getElementById('profile-messages-container');
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('CEP não encontrado. Verifique o CEP digitado.', messagesContainer);
                } else {
                    alert('CEP não encontrado. Verifique o CEP digitado.');
                }
            }
            return null;
        }
        return { 
            street: data.logradouro || '', 
            district: data.bairro || '', 
            city: data.localidade || '', 
            state: data.uf || '', 
            cep: data.cep || cleanCEP 
        };
    } catch (error) {
        console.error('[Perfil] Erro ao buscar CEP na ViaCEP:', error);
        if (window.MessageHelper) {
            window.MessageHelper.showError('Erro ao buscar CEP. Verifique sua conexão e tente novamente.', document.getElementById('new-address-form'));
        } else {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Erro ao buscar CEP. Verifique sua conexão e tente novamente.', messagesContainer);
            } else {
                alert('Erro ao buscar CEP. Verifique sua conexão e tente novamente.');
            }
        }
        return null;
    }
}

// Função para preencher endereço automaticamente
async function fillAddressByCEP(cep) {
    if (!cep || cep.replace(/\D/g, '').length !== 8) return;
    
    const cepInput = document.getElementById('address-cep');
    const buscarCepBtn = document.getElementById('buscar-cep-btn');
    const streetInput = document.getElementById('address-street');
    const neighborhoodInput = document.getElementById('address-neighborhood');
    const cityInput = document.getElementById('address-city');
    const stateSelect = document.getElementById('address-state');
    const numberInput = document.getElementById('address-number');
    
    if (!cepInput) return;
    
    const originalPlaceholder = cepInput.placeholder;
    cepInput.disabled = true;
    cepInput.placeholder = 'Buscando endereço...';
    
    if (buscarCepBtn) {
        buscarCepBtn.disabled = true;
        buscarCepBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Buscando...';
    }
    
    try {
        const addressData = await fetchAddressByCEP(cep);
        if (addressData) {
            if (streetInput) streetInput.value = addressData.street;
            if (neighborhoodInput) neighborhoodInput.value = addressData.district;
            if (cityInput) cityInput.value = addressData.city;
            if (stateSelect && addressData.state) stateSelect.value = addressData.state;
            const formattedCEP = addressData.cep.replace(/^(\d{5})(\d{3})$/, '$1-$2');
            cepInput.value = formattedCEP;
            if (numberInput) setTimeout(() => numberInput.focus(), 100);
        }
    } catch (error) {
        console.error('[Perfil] Erro ao preencher endereço:', error);
    } finally {
        cepInput.disabled = false;
        cepInput.placeholder = originalPlaceholder;
        if (buscarCepBtn) {
            buscarCepBtn.disabled = false;
            buscarCepBtn.innerHTML = '<i class="fas fa-search"></i> Buscar';
        }
    }
}

async function addNewAddress() {
    const type = document.getElementById('address-type').value;
    const zipcode = document.getElementById('address-cep').value;
    const street = document.getElementById('address-street').value;
    const number = document.getElementById('address-number').value;
    const complement = document.getElementById('address-complement').value;
    const neighborhood = document.getElementById('address-neighborhood').value;
    const city = document.getElementById('address-city').value;
    const state = document.getElementById('address-state').value;
    const phone = document.getElementById('address-phone').value;
    
    // Validação básica
    if (!street || !number || !neighborhood || !city || !state || !zipcode) {
        if (window.MessageHelper) {
            window.MessageHelper.showError('Por favor, preencha todos os campos obrigatórios do endereço (rua, número, bairro, cidade, estado, CEP).', document.getElementById('new-address-form'));
        } else {
        const messagesContainer = document.getElementById('profile-messages-container');
        if (messagesContainer && window.MessageHelper) {
            window.MessageHelper.showError('Por favor, preencha todos os campos obrigatórios do endereço (rua, número, bairro, cidade, estado, CEP).', messagesContainer);
        } else {
        alert('Por favor, preencha todos os campos obrigatórios do endereço (rua, número, bairro, cidade, estado, CEP).');
        }
        }
        return;
    }
    
    const currentUser = auth.currentUser;
    if (!currentUser) {
        if (window.MessageHelper) {
            window.MessageHelper.showError('Você precisa estar logado para adicionar um endereço.', document.getElementById('new-address-form'));
        } else {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Você precisa estar logado para adicionar um endereço.', messagesContainer);
            } else {
                alert('Você precisa estar logado para adicionar um endereço.');
            }
        }
        return;
    }
    
    const addressData = {
        type: type,
        zipcode: zipcode,
        street: street,
        number: number,
        complement: complement,
        neighborhood: neighborhood,
        city: city,
        state: state,
        phone: phone,
        isDefault: usuario.addresses && usuario.addresses.length === 0 && !editingAddressId
    };
    
    const saveBtn = document.getElementById('save-new-address');
    const originalText = saveBtn ? saveBtn.innerHTML : '';
    
    try {
        const idToken = await currentUser.getIdToken();
        
        if (saveBtn) {
            if (window.LoadingHelper) {
                window.LoadingHelper.setButtonLoading(saveBtn, editingAddressId ? 'Atualizando...' : 'Salvando...');
            } else {
                saveBtn.disabled = true;
                saveBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${editingAddressId ? 'Atualizando...' : 'Salvando...'}`;
            }
        }
        
        let response;
        if (editingAddressId) {
            // Atualizar endereço existente
            response = await fetch(`/api/addresses/${editingAddressId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify(addressData)
            });
        } else {
            // Verificar limite de 4 endereços apenas ao criar novo
            if (usuario.addresses && usuario.addresses.length >= 4) {
                throw new Error('Você já possui o máximo de 4 endereços cadastrados. Remova um endereço antes de adicionar outro.');
            }
            
            // Criar novo endereço
            response = await fetch('/api/addresses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify(addressData)
            });
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.erro || 'Erro ao salvar endereço');
        }
        
        // Recarregar endereços do backend
        await loadAddressesFromBackend();
        
        document.getElementById('new-address-form').reset();
        toggleNewAddressForm();
        
        if (window.MessageHelper) {
            window.MessageHelper.showSuccess(editingAddressId ? 'Endereço atualizado com sucesso!' : 'Endereço adicionado com sucesso!', document.getElementById('addresses-list'), 3000);
        } else {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess(editingAddressId ? 'Endereço atualizado com sucesso!' : 'Endereço adicionado com sucesso!', messagesContainer, 3000);
            } else {
                alert(editingAddressId ? 'Endereço atualizado com sucesso!' : 'Endereço adicionado com sucesso!');
            }
        }
        
        editingAddressId = null;
        
    } catch (error) {
        console.error('Erro ao salvar endereço:', error);
        if (window.MessageHelper) {
            window.MessageHelper.showError('Erro ao salvar endereço: ' + error.message, document.getElementById('new-address-form'));
        } else {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Erro ao salvar endereço: ' + error.message, messagesContainer);
            } else {
                alert('Erro ao salvar endereço: ' + error.message);
            }
        }
    } finally {
        if (saveBtn && originalText) {
            if (window.LoadingHelper) {
                window.LoadingHelper.restoreButton(saveBtn, { innerHTML: originalText });
            } else {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
            }
        }
    }
}

// Função para carregar endereços do backend
async function loadAddressesFromBackend() {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    
    try {
        const idToken = await currentUser.getIdToken();
        const response = await fetch('/api/addresses', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("Endereços carregados do backend (resultado completo):", result);
            console.log("Tipo de result.addresses:", typeof result.addresses, Array.isArray(result.addresses));
            
            if (result.addresses && Array.isArray(result.addresses)) {
                // Os endereços já vêm no formato correto do backend
                usuario.addresses = result.addresses;
                console.log("Endereços atribuídos ao usuario:", usuario.addresses);
                console.log("Quantidade de endereços:", usuario.addresses.length);
                if (usuario.addresses.length > 0) {
                    console.log("Primeiro endereço:", usuario.addresses[0]);
                }
                renderAddresses();
            } else {
                console.log("Nenhum endereço encontrado ou formato inválido. result.addresses:", result.addresses);
                usuario.addresses = [];
                renderAddresses();
            }
        } else {
            const errorText = await response.text();
            console.error("Erro ao carregar endereços:", response.status, response.statusText, errorText);
        }
    } catch (error) {
        console.error('Erro ao carregar endereços:', error);
    }
}

function renderAddresses() {
    const container = document.getElementById('addresses-list');
    
    if (!container) {
        console.error("Container 'addresses-list' não encontrado!");
        return;
    }
    
    console.log("Renderizando endereços. Total:", usuario.addresses ? usuario.addresses.length : 0);
    console.log("Endereços:", usuario.addresses);
    
    if (!usuario.addresses || usuario.addresses.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-map-marked-alt"></i>
                <h3>Nenhum endereço cadastrado</h3>
                <p>Adicione um endereço para facilitar suas compras.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    console.log("Iniciando renderização de", usuario.addresses.length, "endereços");
    usuario.addresses.forEach((address, index) => {
        console.log(`Renderizando endereço ${index + 1}:`, address);
        const typeText = { 'home': 'Casa', 'work': 'Trabalho', 'other': 'Outro' }[address.type] || 'Endereço';
        const formattedCep = address.zipcode ? address.zipcode.replace(/^(\d{5})(\d{3})$/, '$1-$2') : 'Não informado';
        
        html += `
            <div class="address-card ${address.isDefault ? 'default' : ''}" data-id="${address.id}">
                <div class="address-header">
                    <h4><i class="fas fa-${address.type === 'home' ? 'home' : (address.type === 'work' ? 'briefcase' : 'map-marker-alt')}"></i> ${typeText}</h4>
                    ${address.isDefault ? '<span class="default-badge">Padrão</span>' : ''}
                </div>
                <div class="address-details">
                    <p>${address.street || ''}, ${address.number || ''}${address.complement ? ', ' + address.complement : ''}</p>
                    <p>${address.neighborhood || ''} - ${address.city || ''}/${address.state || ''}</p>
                    <p>CEP: ${formattedCep}</p>
                    ${address.phone ? `<p>Telefone: ${address.phone}</p>` : ''}
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
    console.log("HTML gerado (primeiros 500 chars):", html.substring(0, 500));
    console.log("Tamanho total do HTML:", html.length, "caracteres");
    container.innerHTML = html;
    console.log("HTML inserido no container. Container agora tem:", container.innerHTML.length, "caracteres");
    console.log("Container após inserção (primeiros 500 chars):", container.innerHTML.substring(0, 500));
    
    // Configura os event listeners para os botões dos endereços recém-renderizados.
    setupAddressButtons(); 
}

function setupAddressButtons() {
    // Adiciona listener para o botão "Tornar padrão"
    document.querySelectorAll('.set-default').forEach(button => {
        button.addEventListener('click', async function() {
            const addressId = parseInt(this.dataset.id); 
            const address = usuario.addresses.find(addr => addr.id === addressId);
            if (!address) return;
            
            const currentUser = auth.currentUser;
            if (!currentUser) {
                if (window.MessageHelper) {
                    window.MessageHelper.showError('Você precisa estar logado.', document.getElementById('addresses-list'));
                } else {
                    const messagesContainer = document.getElementById('profile-messages-container');
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError('Você precisa estar logado.', messagesContainer);
                    } else {
                        alert('Você precisa estar logado.');
                    }
                }
                return;
            }
            
            try {
                const idToken = await currentUser.getIdToken();
                const response = await fetch(`/api/addresses/${addressId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${idToken}`
                    },
                    body: JSON.stringify({
                        ...address,
                        isDefault: true
                    })
                });
                
                if (response.ok) {
                    await loadAddressesFromBackend();
                    if (window.MessageHelper) {
                        window.MessageHelper.showSuccess('Endereço definido como padrão!', document.getElementById('addresses-list'), 3000);
                    }
                } else {
                    throw new Error('Erro ao atualizar endereço padrão');
                }
            } catch (error) {
                console.error('Erro ao definir endereço padrão:', error);
                if (window.MessageHelper) {
                    window.MessageHelper.showError('Erro ao definir endereço padrão: ' + error.message, document.getElementById('addresses-list'));
                } else {
                    const messagesContainer = document.getElementById('profile-messages-container');
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError('Erro ao definir endereço padrão: ' + error.message, messagesContainer);
                    } else {
                        alert('Erro ao definir endereço padrão: ' + error.message);
                    }
                }
            }
        });
    });
    
    // Adiciona listener para o botão "Editar" endereço
    document.querySelectorAll('.edit-address').forEach(button => {
        button.addEventListener('click', function() {
            const addressId = parseInt(this.dataset.id);
            const address = usuario.addresses.find(addr => addr.id === addressId);
            if (!address) return;
            
            // Preenche o formulário com os dados do endereço para edição
            document.getElementById('address-type').value = address.type;
            document.getElementById('address-cep').value = address.zipcode ? address.zipcode.replace(/^(\d{5})(\d{3})$/, '$1-$2') : '';
            document.getElementById('address-street').value = address.street || '';
            document.getElementById('address-number').value = address.number || '';
            document.getElementById('address-complement').value = address.complement || '';
            document.getElementById('address-neighborhood').value = address.neighborhood || '';
            document.getElementById('address-city').value = address.city || '';
            document.getElementById('address-state').value = address.state || '';
            document.getElementById('address-phone').value = address.phone || '';
            
            editingAddressId = addressId; // Marcar que está editando
            toggleNewAddressForm(); // Mostra o formulário para edição
        });
    });
    
    // Adiciona listener para o botão "Excluir" endereço
    document.querySelectorAll('.delete-address').forEach(button => {
        button.addEventListener('click', async function() {
            if (!confirm('Tem certeza que deseja excluir este endereço?')) return;
            
            const addressId = parseInt(this.dataset.id);
            const currentUser = auth.currentUser;
            if (!currentUser) {
                if (window.MessageHelper) {
                    window.MessageHelper.showError('Você precisa estar logado.', document.getElementById('addresses-list'));
                } else {
                    const messagesContainer = document.getElementById('profile-messages-container');
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError('Você precisa estar logado.', messagesContainer);
                    } else {
                        alert('Você precisa estar logado.');
                    }
                }
                return;
            }
            
            try {
                const idToken = await currentUser.getIdToken();
                const response = await fetch(`/api/addresses/${addressId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${idToken}`
                    }
                });
                
                if (response.ok) {
                    await loadAddressesFromBackend();
                    if (window.MessageHelper) {
                        window.MessageHelper.showSuccess('Endereço removido com sucesso!', document.getElementById('addresses-list'), 3000);
                    } else {
                        const messagesContainer = document.getElementById('profile-messages-container');
                        if (messagesContainer && window.MessageHelper) {
                            window.MessageHelper.showSuccess('Endereço removido com sucesso!', messagesContainer, 3000);
                        } else {
                            alert('Endereço removido com sucesso!');
                        }
                    }
                } else {
                    const result = await response.json();
                    throw new Error(result.erro || 'Erro ao remover endereço');
                }
            } catch (error) {
                console.error('Erro ao remover endereço:', error);
                if (window.MessageHelper) {
                    window.MessageHelper.showError('Erro ao remover endereço: ' + error.message, document.getElementById('addresses-list'));
                } else {
                    const messagesContainer = document.getElementById('profile-messages-container');
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError('Erro ao remover endereço: ' + error.message, messagesContainer);
                    } else {
                        alert('Erro ao remover endereço: ' + error.message);
                    }
                }
            }
        });
    });
}

// Função para carregar pedidos do usuário
async function loadUserOrders() {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    
    try {
        const idToken = await currentUser.getIdToken();
        const response = await fetch('/api/orders', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.orders && Array.isArray(result.orders)) {
                renderOrders(result.orders);
            } else {
                renderOrders([]);
            }
        } else {
            console.error("Erro ao carregar pedidos:", response.status, response.statusText);
            renderOrders([]);
        }
    } catch (error) {
        console.error('Erro ao carregar pedidos:', error);
        renderOrders([]);
    }
}

// Função para renderizar pedidos
function renderOrders(orders) {
    const container = document.getElementById('orders-section');
    if (!container) return;
    
    const ordersContainer = document.getElementById('orders-container') || container;
    
    if (orders.length === 0) {
        ordersContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shopping-basket"></i>
                <h3>Nenhum pedido encontrado</h3>
                <p>Você ainda não realizou nenhum pedido em nossa loja. Aproveite para conhecer nossos produtos!</p>
                <a href="/produtos" class="btn-shop-now">
                    <i class="fas fa-shopping-bag"></i> Ir para a Loja
                </a>
            </div>
        `;
        return;
    }
    
    let html = '<div class="orders-list">';
    
    // Função auxiliar para formatar datas de forma segura (fora do loop)
    function formatOrderDate(dateString, includeTime = true) {
        if (!dateString) {
            console.warn('Data vazia ou nula');
            return 'Data não disponível';
        }
        
        try {
            // Se a string parece ser uma data inválida ou muito antiga, retornar mensagem
            if (typeof dateString === 'string' && dateString.includes('1960')) {
                console.warn('Data suspeita (1960):', dateString);
                return 'Data não disponível';
            }
            
            // Tentar parse da data
            let date;
            if (typeof dateString === 'string') {
                // Se tem timezone no formato ISO, usar diretamente
                if (dateString.includes('T') || dateString.includes('+') || dateString.includes('-') && dateString.length > 10) {
                    date = new Date(dateString);
                } else {
                    // Tentar adicionar timezone se não tiver
                    date = new Date(dateString + (dateString.includes('T') ? '' : 'T00:00:00-03:00'));
                }
            } else {
                date = new Date(dateString);
            }
            
            // Verificar se a data é válida e não é muito antiga (antes de 1970)
            if (isNaN(date.getTime())) {
                console.error('Data inválida (NaN):', dateString);
                return 'Data não disponível';
            }
            
            if (date.getFullYear() < 1970) {
                console.error('Data muito antiga:', dateString, 'Ano:', date.getFullYear());
                return 'Data não disponível';
            }
            
            const options = {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
                timeZone: 'America/Sao_Paulo'
            };
            
            if (includeTime) {
                options.hour = '2-digit';
                options.minute = '2-digit';
            }
            
            return date.toLocaleDateString('pt-BR', options);
        } catch (e) {
            console.error('Erro ao formatar data:', e, dateString, typeof dateString);
            return 'Data não disponível';
        }
    }
    
    orders.forEach(order => {
        const formattedDate = formatOrderDate(order.data_venda, true);
        
        const totalItems = order.itens.reduce((sum, item) => sum + item.quantidade, 0);
        
        // Normalizar status para formato de classe CSS (remover espaços e converter para minúsculas)
        const statusClass = (order.status || '').toLowerCase().replace(/\s+/g, '-').replace(/_/g, '-');
        
        html += `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-info">
                        <h3>Pedido ${order.codigo_pedido}</h3>
                        <span class="order-date">${formattedDate}</span>
                    </div>
                    <div class="order-status-badge status-${statusClass}">
                        ${order.status_display || order.status || 'Desconhecido'}
                    </div>
                </div>
                <div class="order-details">
                    <div class="order-items">
                        <p class="order-items-count">${totalItems} ${totalItems === 1 ? 'item' : 'itens'}</p>
                        <ul class="order-items-list">
                            ${order.itens.map(item => `
                                <li>
                                    <span class="item-quantity">${item.quantidade}x</span>
                                    <span class="item-name">${item.nome_produto}</span>
                                    <span class="item-price">R$ ${item.subtotal.toFixed(2).replace('.', ',')}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div class="order-summary">
                        <div class="summary-row">
                            <span>Subtotal:</span>
                            <span>R$ ${(order.valor_total - order.valor_frete + order.valor_desconto).toFixed(2).replace('.', ',')}</span>
                        </div>
                        ${order.valor_frete > 0 ? `
                            <div class="summary-row">
                                <span>Frete:</span>
                                <span>R$ ${order.valor_frete.toFixed(2).replace('.', ',')}</span>
                            </div>
                        ` : ''}
                        ${order.valor_desconto > 0 ? `
                            <div class="summary-row discount">
                                <span>Desconto:</span>
                                <span>- R$ ${order.valor_desconto.toFixed(2).replace('.', ',')}</span>
                            </div>
                        ` : ''}
                        <div class="summary-row total">
                            <span><strong>Total:</strong></span>
                            <span><strong>R$ ${order.valor_total.toFixed(2).replace('.', ',')}</strong></span>
                        </div>
                    </div>
                    <div class="order-address">
                        <p><strong>Endereço de entrega:</strong></p>
                        <p>${order.endereco.rua}, ${order.endereco.numero}${order.endereco.complemento ? ', ' + order.endereco.complemento : ''}</p>
                        <p>${order.endereco.bairro} - ${order.endereco.cidade}/${order.endereco.estado}</p>
                        <p>CEP: ${order.endereco.cep.replace(/^(\d{5})(\d{3})$/, '$1-$2')}</p>
                    </div>
                    ${order.data_envio ? `
                        <div class="order-tracking">
                            <p><i class="fas fa-truck"></i> Enviado em: ${formatOrderDate(order.data_envio, false)}</p>
                        </div>
                    ` : ''}
                    ${order.data_entrega_real ? `
                        <div class="order-delivered">
                            <p><i class="fas fa-check-circle"></i> Entregue em: ${formatOrderDate(order.data_entrega_real, false)}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    html += '</div>';
    ordersContainer.innerHTML = html;
}

// =====================================================
// FUNÇÕES DE DADOS FISCAIS
// =====================================================

// Função para formatar CPF
function formatCPF(value) {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
        return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return value;
}

// Função para formatar CNPJ
function formatCNPJ(value) {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 14) {
        return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return value;
}

// Função para formatar CEP
function formatCEP(value) {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 8) {
        return numbers.replace(/(\d{5})(\d{3})/, '$1-$2');
    }
    return value;
}

// Função para carregar dados fiscais
async function loadFiscalData() {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    
    const fiscalForm = document.getElementById('fiscal-form');
    const fiscalDisplay = document.getElementById('fiscal-data-display');
    const fiscalEmptyState = document.getElementById('fiscal-empty-state');
    
    try {
        const idToken = await currentUser.getIdToken();
        const response = await fetch('/api/fiscal-data', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.fiscal_data) {
                // Há dados fiscais salvos - mostrar modo de visualização
                renderFiscalDataDisplay(result.fiscal_data);
                populateFiscalForm(result.fiscal_data);
                fiscalDisplay.style.display = 'block';
                fiscalForm.style.display = 'none';
                fiscalEmptyState.style.display = 'none';
            } else {
                // Não há dados fiscais - mostrar estado vazio
                fiscalDisplay.style.display = 'none';
                fiscalForm.style.display = 'none';
                fiscalEmptyState.style.display = 'block';
                document.getElementById('fiscal-form').reset();
            }
        } else {
            console.error("Erro ao carregar dados fiscais:", response.status);
            fiscalDisplay.style.display = 'none';
            fiscalForm.style.display = 'none';
            fiscalEmptyState.style.display = 'block';
        }
    } catch (error) {
        console.error('Erro ao carregar dados fiscais:', error);
        fiscalDisplay.style.display = 'none';
        fiscalForm.style.display = 'none';
        fiscalEmptyState.style.display = 'block';
    }
}

// Função para renderizar a visualização dos dados fiscais
function renderFiscalDataDisplay(data) {
    // Nome/Razão Social
    document.getElementById('display-fiscal-nome-razao-social').textContent = data.nome_razao_social || '-';
    
    // Tipo e CPF (sempre CPF)
    document.getElementById('display-fiscal-tipo').textContent = 'CPF';
    const cpfFormatted = formatCPF(data.cpf_cnpj || '');
    document.getElementById('display-fiscal-cpf-cnpj').textContent = cpfFormatted || '-';
    
    // Endereço completo - verificar se endereco é um objeto ou se os campos estão no nível raiz
    const endereco = data.endereco || {};
    const rua = endereco.rua || data.rua;
    const numero = endereco.numero || data.numero;
    const complemento = endereco.complemento || data.complemento;
    const bairro = endereco.bairro || data.bairro;
    const cidade = endereco.cidade || data.cidade;
    const estado = endereco.estado || data.estado;
    const cep = endereco.cep || data.cep;
    
    let enderecoCompleto = '';
    if (rua && numero) {
        enderecoCompleto = `${rua}, ${numero}`;
        if (complemento) {
            enderecoCompleto += ` - ${complemento}`;
        }
        enderecoCompleto += `\n${bairro || ''} - ${cidade || ''}/${estado || ''}`;
        if (cep) {
            enderecoCompleto += `\nCEP: ${formatCEP(cep)}`;
        }
    } else {
        enderecoCompleto = 'Endereço não informado';
    }
    document.getElementById('display-fiscal-endereco-completo').innerHTML = enderecoCompleto.replace(/\n/g, '<br>');
    
    // Inscrições removidas (só para CNPJ)
    document.getElementById('display-fiscal-inscricoes').style.display = 'none';
}

// Função para preencher formulário com dados fiscais
function populateFiscalForm(data) {
    // Sempre usar CPF (removido suporte a CNPJ)
    const cpfCnpj = data.cpf_cnpj || '';
    document.getElementById('fiscal-cpf-cnpj').value = formatCPF(cpfCnpj);
    document.getElementById('fiscal-nome').value = data.nome_razao_social || '';
    
    // Verificar se endereco é um objeto ou se os campos estão no nível raiz
    const endereco = data.endereco || {};
    document.getElementById('fiscal-rua').value = endereco.rua || data.rua || '';
    document.getElementById('fiscal-numero').value = endereco.numero || data.numero || '';
    document.getElementById('fiscal-complemento').value = endereco.complemento || data.complemento || '';
    document.getElementById('fiscal-bairro').value = endereco.bairro || data.bairro || '';
    document.getElementById('fiscal-cidade').value = endereco.cidade || data.cidade || '';
    document.getElementById('fiscal-estado').value = endereco.estado || data.estado || '';
    const cep = endereco.cep || data.cep || '';
    document.getElementById('fiscal-cep').value = cep ? formatCEP(cep) : '';
}

// Função para salvar dados fiscais
async function saveFiscalData(event) {
    event.preventDefault();
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    
    const saveBtn = document.getElementById('save-fiscal-btn');
    const messageDiv = document.getElementById('fiscal-message');
    
    try {
        const idToken = await currentUser.getIdToken();
        
        // Coletar dados do formulário
        const cpfCnpj = document.getElementById('fiscal-cpf-cnpj').value.replace(/\D/g, '');
        const nomeRazaoSocial = document.getElementById('fiscal-nome').value.trim();
        
        const fiscalData = {
            tipo: 'CPF', // Sempre CPF (removido suporte a CNPJ)
            cpf_cnpj: cpfCnpj,
            nome_razao_social: nomeRazaoSocial,
            inscricao_estadual: null, // Removido (só para CNPJ)
            inscricao_municipal: null, // Removido (só para CNPJ)
            endereco: {
                rua: document.getElementById('fiscal-rua').value.trim(),
                numero: document.getElementById('fiscal-numero').value.trim(),
                complemento: document.getElementById('fiscal-complemento').value.trim(),
                bairro: document.getElementById('fiscal-bairro').value.trim(),
                cidade: document.getElementById('fiscal-cidade').value.trim(),
                estado: document.getElementById('fiscal-estado').value,
                cep: document.getElementById('fiscal-cep').value.replace(/\D/g, '')
            }
        };
        
        let loadingState = null;
        if (window.LoadingHelper && window.LoadingHelper.setButtonLoading) {
            loadingState = window.LoadingHelper.setButtonLoading(saveBtn, 'Salvando...');
            if (loadingState) {
                saveBtn.dataset.loadingState = JSON.stringify(loadingState);
            }
        } else {
            saveBtn.disabled = true;
            const originalHTML = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
            saveBtn.dataset.originalHTML = originalHTML;
        }
        
        const response = await fetch('/api/fiscal-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify(fiscalData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Mostrar mensagem de sucesso
            if (window.MessageHelper) {
                window.MessageHelper.showSuccess('✅ Dados fiscais salvos com sucesso!', messageDiv);
            } else {
                messageDiv.className = 'message success';
                messageDiv.textContent = '✅ Dados fiscais salvos com sucesso!';
                messageDiv.style.display = 'block';
            }
            
            // Recarregar dados e mudar para modo de visualização
            await loadFiscalData();
            
            // Esconder botão cancelar
            const cancelBtn = document.getElementById('cancel-fiscal-edit-btn');
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            // Esconder mensagem após 4 segundos
            setTimeout(() => {
                if (messageDiv) {
                    messageDiv.style.display = 'none';
                }
            }, 4000);
        } else {
            if (window.MessageHelper) {
                window.MessageHelper.showError(result.erro || 'Erro ao salvar dados fiscais', messageDiv);
            } else {
                messageDiv.className = 'message error';
                messageDiv.textContent = result.erro || 'Erro ao salvar dados fiscais';
                messageDiv.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Erro ao salvar dados fiscais:', error);
        if (window.MessageHelper) {
            window.MessageHelper.showError('Erro ao salvar dados fiscais. Tente novamente.', messageDiv);
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = 'Erro ao salvar dados fiscais. Tente novamente.';
            messageDiv.style.display = 'block';
        }
    } finally {
        // Restaurar botão
        if (window.LoadingHelper && window.LoadingHelper.restoreButton && saveBtn.dataset.loadingState) {
            try {
                const state = JSON.parse(saveBtn.dataset.loadingState);
                if (state && state.originalHTML !== undefined && state.originalDisabled !== undefined) {
                    window.LoadingHelper.restoreButton(saveBtn, state);
                } else {
                    // Fallback se o state não estiver no formato correto
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = saveBtn.dataset.originalHTML || '<i class="fas fa-save"></i> Salvar Dados Fiscais';
                    saveBtn.classList.remove('loading');
                }
            } catch (e) {
                console.error('Erro ao restaurar botão:', e);
                saveBtn.disabled = false;
                saveBtn.innerHTML = saveBtn.dataset.originalHTML || '<i class="fas fa-save"></i> Salvar Dados Fiscais';
                saveBtn.classList.remove('loading');
            }
            saveBtn.removeAttribute('data-loading-state');
            saveBtn.removeAttribute('data-original-html');
        } else {
            saveBtn.disabled = false;
            saveBtn.innerHTML = saveBtn.dataset.originalHTML || '<i class="fas fa-save"></i> Salvar Dados Fiscais';
            saveBtn.classList.remove('loading');
            saveBtn.removeAttribute('data-loading-state');
            saveBtn.removeAttribute('data-original-html');
        }
    }
}

// Função para deletar dados fiscais
async function deleteFiscalData() {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    
    const deleteBtn = document.getElementById('delete-fiscal-btn');
    const messageDiv = document.getElementById('fiscal-message');
    
    try {
        const idToken = await currentUser.getIdToken();
        
        let deleteLoadingState = null;
        if (window.LoadingHelper && window.LoadingHelper.setButtonLoading) {
            deleteLoadingState = window.LoadingHelper.setButtonLoading(deleteBtn, 'Removendo...');
            if (deleteLoadingState) {
                deleteBtn.dataset.loadingState = JSON.stringify(deleteLoadingState);
            }
        } else {
            deleteBtn.disabled = true;
            const originalHTML = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Removendo...';
            deleteBtn.dataset.originalHTML = originalHTML;
        }
        
        const response = await fetch('/api/fiscal-data', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (window.MessageHelper) {
                window.MessageHelper.showSuccess('✅ Dados fiscais removidos com sucesso!', messageDiv);
            } else {
                messageDiv.className = 'message success';
                messageDiv.textContent = '✅ Dados fiscais removidos com sucesso!';
                messageDiv.style.display = 'block';
            }
            
            // Recarregar dados e mostrar estado vazio
            await loadFiscalData();
            
            // Esconder mensagem após 4 segundos
            setTimeout(() => {
                if (messageDiv) {
                    messageDiv.style.display = 'none';
                }
            }, 4000);
        } else {
            if (window.MessageHelper) {
                window.MessageHelper.showError(result.erro || 'Erro ao remover dados fiscais', messageDiv);
            } else {
                messageDiv.className = 'message error';
                messageDiv.textContent = result.erro || 'Erro ao remover dados fiscais';
                messageDiv.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Erro ao remover dados fiscais:', error);
        if (window.MessageHelper) {
            window.MessageHelper.showError('Erro ao remover dados fiscais. Tente novamente.', messageDiv);
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = 'Erro ao remover dados fiscais. Tente novamente.';
            messageDiv.style.display = 'block';
        }
    } finally {
        // Restaurar botão
        if (window.LoadingHelper && window.LoadingHelper.restoreButton && deleteBtn.dataset.loadingState) {
            try {
                const state = JSON.parse(deleteBtn.dataset.loadingState);
                if (state && state.originalHTML !== undefined && state.originalDisabled !== undefined) {
                    window.LoadingHelper.restoreButton(deleteBtn, state);
                } else {
                    // Fallback se o state não estiver no formato correto
                    deleteBtn.disabled = false;
                    deleteBtn.innerHTML = deleteBtn.dataset.originalHTML || '<i class="fas fa-trash"></i> Remover Dados Fiscais';
                    deleteBtn.classList.remove('loading');
                }
            } catch (e) {
                console.error('Erro ao restaurar botão:', e);
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = deleteBtn.dataset.originalHTML || '<i class="fas fa-trash"></i> Remover Dados Fiscais';
                deleteBtn.classList.remove('loading');
            }
            deleteBtn.removeAttribute('data-loading-state');
            deleteBtn.removeAttribute('data-original-html');
        } else {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = deleteBtn.dataset.originalHTML || '<i class="fas fa-trash"></i> Remover Dados Fiscais';
            deleteBtn.classList.remove('loading');
            deleteBtn.removeAttribute('data-loading-state');
            deleteBtn.removeAttribute('data-original-html');
        }
    }
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

                const response = await fetch("/api/user_data", {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${idToken}` // Envia o token para autenticação no backend
                    }
                });

                if (!response.ok) {
                    // Trata respostas HTTP que não são sucesso (ex: 401, 404, 500)
                    if (response.status === 401) {
                        const messagesContainer = document.getElementById('profile-messages-container');
                        if (messagesContainer && window.MessageHelper) {
                            window.MessageHelper.showError("Sessão expirada ou não autorizada. Por favor, faça login novamente.", messagesContainer);
                            setTimeout(() => {
                                window.location.href = '/auth/login';
                            }, 2000);
                        } else {
                        alert("Sessão expirada ou não autorizada. Por favor, faça login novamente.");
                            window.location.href = '/auth/login';
                        }
                    } else {
                        const errorData = await response.json(); // Tenta ler o JSON de erro do backend
                        throw new Error(errorData.erro || "Erro desconhecido ao carregar dados do perfil.");
                    }
                }

                const data = await response.json(); // Parseia a resposta JSON
                console.log("Dados do perfil carregados do backend:", data);
                loadUserData(data); // Carrega os dados recebidos e atualiza a UI
                // Carregar endereços separadamente para garantir que estão atualizados
                await loadAddressesFromBackend();
                
                // Garantir que os endereços sejam renderizados mesmo se não vierem nos dados iniciais
                if (!usuario.addresses || usuario.addresses.length === 0) {
                    console.log("Nenhum endereço nos dados iniciais, tentando carregar do backend...");
                    await loadAddressesFromBackend();
                }
                
                // Carregar pedidos do usuário
                await loadUserOrders();
                
                // Carregar dados fiscais
                await loadFiscalData();

            } catch (error) {
                console.error("Erro ao carregar o perfil:", error);
                const messagesContainer = document.getElementById('profile-messages-container');
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError("Ocorreu um erro ao carregar seu perfil. Por favor, tente novamente mais tarde.", messagesContainer);
                } else {
                alert("Ocorreu um erro ao carregar seu perfil. Por favor, tente novamente mais tarde.");
                }
                // Opcional: Redirecionar ou deslogar o usuário em caso de erro grave.
            }
        } else {
            // Usuário não logado no Firebase, redireciona para a página de login.
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Você precisa estar logado para acessar esta página.', messagesContainer);
                setTimeout(() => {
                    window.location.href = '/auth/login';
                }, 2000);
            } else {
            alert('Você precisa estar logado para acessar esta página.');
                window.location.href = '/auth/login';
            } 
        }
    });

    // --- Configuração dos Listeners de Evento para os botões ---
    // Estes listeners são configurados uma única vez, após o DOM estar pronto.

    // Botões de informações pessoais
    // CORRIGIDO: Usando os IDs corretos do HTML, e removendo as declarações duplicadas.
    document.getElementById('edit-btn').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('cancel-btn').addEventListener('click', togglePersonalInfoEdit);
    document.getElementById('save-btn').addEventListener('click', savePersonalInfo);

    // Event listeners para dados fiscais
    const fiscalForm = document.getElementById('fiscal-form');
    if (fiscalForm) {
        fiscalForm.addEventListener('submit', saveFiscalData);
    }
    
    // Botão de editar dados fiscais
    const editFiscalBtn = document.getElementById('edit-fiscal-btn');
    if (editFiscalBtn) {
        editFiscalBtn.addEventListener('click', () => {
            const fiscalForm = document.getElementById('fiscal-form');
            const fiscalDisplay = document.getElementById('fiscal-data-display');
            const cancelBtn = document.getElementById('cancel-fiscal-edit-btn');
            
            fiscalDisplay.style.display = 'none';
            fiscalForm.style.display = 'block';
            if (cancelBtn) cancelBtn.style.display = 'inline-block';
        });
    }
    
    // Botão de cancelar edição
    const cancelFiscalEditBtn = document.getElementById('cancel-fiscal-edit-btn');
    if (cancelFiscalEditBtn) {
        cancelFiscalEditBtn.addEventListener('click', () => {
            const fiscalForm = document.getElementById('fiscal-form');
            const fiscalDisplay = document.getElementById('fiscal-data-display');
            const fiscalEmptyState = document.getElementById('fiscal-empty-state');
            const cancelBtn = document.getElementById('cancel-fiscal-edit-btn');
            
            // Recarregar dados para restaurar valores originais ou voltar ao estado inicial
            loadFiscalData();
            if (cancelBtn) cancelBtn.style.display = 'none';
        });
    }
    
        // Botão de adicionar dados fiscais (do estado vazio)
        const addFiscalDataBtn = document.getElementById('add-fiscal-data-btn');
        if (addFiscalDataBtn) {
            addFiscalDataBtn.addEventListener('click', () => {
                const fiscalForm = document.getElementById('fiscal-form');
                const fiscalEmptyState = document.getElementById('fiscal-empty-state');
                const cancelBtn = document.getElementById('cancel-fiscal-edit-btn');
                
                fiscalEmptyState.style.display = 'none';
                fiscalForm.style.display = 'block';
                if (cancelBtn) cancelBtn.style.display = 'inline-block';
                
                // Limpar formulário
                document.getElementById('fiscal-form').reset();
            });
        }
    
    // Botão de deletar dados fiscais
    const deleteFiscalBtn = document.getElementById('delete-fiscal-btn');
    if (deleteFiscalBtn) {
        deleteFiscalBtn.addEventListener('click', async () => {
            // Mostrar confirmação inline
            const messageDiv = document.getElementById('fiscal-message');
            if (!messageDiv) return;
            
            messageDiv.innerHTML = `
                <div class="confirmation-dialog">
                    <p>⚠️ Tem certeza que deseja remover seus dados fiscais? Esta ação não pode ser desfeita.</p>
                    <div class="confirmation-actions">
                        <button type="button" class="btn btn-danger" id="confirm-delete-fiscal">
                            <i class="fas fa-trash"></i> Sim, remover
                        </button>
                        <button type="button" class="btn btn-outline" id="cancel-delete-fiscal">
                            <i class="fas fa-times"></i> Cancelar
                        </button>
                    </div>
                </div>
            `;
            messageDiv.style.display = 'block';
            
            // Event listener para confirmar remoção
            const confirmBtn = document.getElementById('confirm-delete-fiscal');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', async () => {
                    messageDiv.style.display = 'none';
                    messageDiv.innerHTML = '';
                    await deleteFiscalData();
                });
            }
            
            // Event listener para cancelar
            const cancelBtn = document.getElementById('cancel-delete-fiscal');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    messageDiv.style.display = 'none';
                    messageDiv.innerHTML = '';
                });
            }
        });
    }
    
    // Máscara de input fiscal (apenas CPF)
    const fiscalCpfCnpjInput = document.getElementById('fiscal-cpf-cnpj');
    if (fiscalCpfCnpjInput) {
        fiscalCpfCnpjInput.addEventListener('input', function() {
            this.value = formatCPF(this.value);
        });
    }
    
    // Função para preencher endereço fiscal automaticamente por CEP
    async function fillFiscalAddressByCEP(cep) {
        if (!cep || cep.replace(/\D/g, '').length !== 8) return;
        
        const cepInput = document.getElementById('fiscal-cep');
        const buscarCepBtn = document.getElementById('buscar-fiscal-cep-btn');
        const streetInput = document.getElementById('fiscal-rua');
        const neighborhoodInput = document.getElementById('fiscal-bairro');
        const cityInput = document.getElementById('fiscal-cidade');
        const stateSelect = document.getElementById('fiscal-estado');
        const numberInput = document.getElementById('fiscal-numero');
        const messageDiv = document.getElementById('fiscal-message');
        
        if (!cepInput) return;
        
        const originalPlaceholder = cepInput.placeholder;
        cepInput.disabled = true;
        cepInput.placeholder = 'Buscando endereço...';
        
        if (buscarCepBtn) {
            buscarCepBtn.disabled = true;
            buscarCepBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Buscando...';
        }
        
        try {
            const addressData = await fetchAddressByCEP(cep);
            if (addressData) {
                if (streetInput) streetInput.value = addressData.street;
                if (neighborhoodInput) neighborhoodInput.value = addressData.district;
                if (cityInput) cityInput.value = addressData.city;
                if (stateSelect && addressData.state) stateSelect.value = addressData.state;
                const formattedCEP = addressData.cep.replace(/^(\d{5})(\d{3})$/, '$1-$2');
                cepInput.value = formattedCEP;
                if (numberInput) setTimeout(() => numberInput.focus(), 100);
                
                if (messageDiv && window.MessageHelper) {
                    window.MessageHelper.showSuccess('Endereço encontrado e preenchido automaticamente!', messageDiv);
                }
            } else {
                if (messageDiv && window.MessageHelper) {
                    window.MessageHelper.showError('CEP não encontrado. Verifique o CEP digitado.', messageDiv);
                }
            }
        } catch (error) {
            console.error('[Perfil] Erro ao preencher endereço fiscal:', error);
            if (messageDiv && window.MessageHelper) {
                window.MessageHelper.showError('Erro ao buscar CEP. Verifique sua conexão e tente novamente.', messageDiv);
            }
        } finally {
            cepInput.disabled = false;
            cepInput.placeholder = originalPlaceholder;
            if (buscarCepBtn) {
                buscarCepBtn.disabled = false;
                buscarCepBtn.innerHTML = '<i class="fas fa-search"></i> Buscar';
            }
        }
    }
    
    const fiscalCepInput = document.getElementById('fiscal-cep');
    const buscarFiscalCepBtn = document.getElementById('buscar-fiscal-cep-btn');
    
    if (fiscalCepInput) {
        fiscalCepInput.addEventListener('input', function() {
            this.value = formatCEP(this.value);
        });
        
        // Busca automática quando o CEP estiver completo
        fiscalCepInput.addEventListener('blur', function(e) {
            const cep = this.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fillFiscalAddressByCEP(cep);
            }
        });
    }
    
    // Event listener para o botão de buscar CEP fiscal
    if (buscarFiscalCepBtn && fiscalCepInput) {
        buscarFiscalCepBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const cep = fiscalCepInput.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fillFiscalAddressByCEP(cep);
            } else {
                const messageDiv = document.getElementById('fiscal-message');
                if (window.MessageHelper) {
                    window.MessageHelper.showError('Por favor, digite um CEP válido (8 dígitos)', messageDiv);
                } else {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = 'Por favor, digite um CEP válido (8 dígitos)';
                    messageDiv.style.display = 'block';
                }
                fiscalCepInput.focus();
            }
        });
    }

    // Botão de logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            const messagesContainer = document.getElementById('profile-messages-container');
            
            if (window.LoadingHelper) {
                window.LoadingHelper.setButtonLoading(logoutBtn, 'Saindo...');
            } else {
                logoutBtn.disabled = true;
                const originalHTML = logoutBtn.innerHTML;
                logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saindo...';
            }
            
            try {
                // Fazer logout do Firebase
                await signOut(auth);
                
                // Fazer logout do backend (limpar sessão)
                const response = await fetch('/auth/logout', {
                    method: 'GET'
                });
                
                // Limpar dados locais
                localStorage.removeItem('cartSessionId');
                usuario = { addresses: [] };
                
                // Redirecionar para login
                window.location.href = '/auth/login';
            } catch (error) {
                console.error('Erro ao fazer logout:', error);
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('Erro ao fazer logout. Tente novamente.', messagesContainer);
                }
                if (window.LoadingHelper) {
                    window.LoadingHelper.restoreButton(logoutBtn, { innerHTML: '<i class="fas fa-sign-out-alt"></i> Sair' });
                } else {
                    logoutBtn.disabled = false;
                    logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Sair';
                }
            }
        });
    }

    // Botões de endereços
    document.getElementById('add-address-btn').addEventListener('click', toggleNewAddressForm);
    document.getElementById('cancel-new-address').addEventListener('click', toggleNewAddressForm);
    document.getElementById('save-new-address').addEventListener('click', addNewAddress);
    
    // Event listeners para busca de CEP
    const cepInput = document.getElementById('address-cep');
    const buscarCepBtn = document.getElementById('buscar-cep-btn');
    
    if (buscarCepBtn && cepInput) {
        buscarCepBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const cep = cepInput.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fillAddressByCEP(cep);
            } else {
                const messageDiv = document.getElementById('address-message') || document.getElementById('fiscal-message');
                if (window.MessageHelper && messageDiv) {
                    window.MessageHelper.showError('Por favor, digite um CEP válido (8 dígitos)', messageDiv);
                } else if (messageDiv) {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = 'Por favor, digite um CEP válido (8 dígitos)';
                    messageDiv.style.display = 'block';
                }
                cepInput.focus();
            }
        });
    }
    
    // Formatação automática do CEP e busca automática
    if (cepInput) {
        // Formatação do CEP (00000-000)
        cepInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 5) {
                value = value.substring(0, 5) + '-' + value.substring(5, 8);
            }
            e.target.value = value;
        });
        
        // Busca automática após digitar 8 dígitos (com delay)
        let cepTimeout;
        cepInput.addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            clearTimeout(cepTimeout);
            if (value.length === 8) {
                cepTimeout = setTimeout(() => {
                    fillAddressByCEP(value);
                }, 800);
            }
        });
        
        // Busca ao perder o foco se tiver 8 dígitos
        cepInput.addEventListener('blur', function(e) {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fillAddressByCEP(cep);
            }
        });
    }
    
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

    // --- Funções de Verificação de Email e Alteração de Senha ---
    
    // Carrega o status de verificação de email
    async function loadEmailVerificationStatus(user) {
        try {
            const idToken = await user.getIdToken(true); // Força refresh para obter status atualizado
            
            const response = await fetch("/api/auth/verify-email-status", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id_token: idToken })
            });

            if (!response.ok) {
                throw new Error("Erro ao verificar status de email");
            }

            const data = await response.json();
            const emailVerified = data.email_verificado;
            const statusText = document.getElementById('email-verification-text');
            const resendBtn = document.getElementById('resend-verification-btn');

            if (emailVerified) {
                statusText.innerHTML = '<span class="email-verified"><i class="fas fa-check-circle"></i> Email verificado</span>';
                resendBtn.style.display = 'none';
            } else {
                statusText.innerHTML = '<span class="email-unverified"><i class="fas fa-exclamation-circle"></i> Email não verificado. Verifique sua caixa de entrada.</span>';
                resendBtn.style.display = 'inline-flex';
            }
        } catch (error) {
            console.error("Erro ao carregar status de verificação:", error);
            document.getElementById('email-verification-text').textContent = "Erro ao verificar status";
        }
    }

    // Reenvia email de verificação
    async function resendVerificationEmail(user) {
        try {
            const idToken = await user.getIdToken();
            
            // Chama Firebase para enviar email
            await sendEmailVerification(user);
            
            // Notifica backend
            await fetch("/api/auth/resend-verification", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id_token: idToken })
            });

            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess("Email de verificação enviado! Verifique sua caixa de entrada e também a pasta de spam.", messagesContainer, 5000);
            } else {
                alert("Email de verificação enviado! Verifique sua caixa de entrada e também a pasta de spam.");
            }
        } catch (error) {
            console.error("Erro ao reenviar verificação:", error);
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro ao enviar email de verificação: " + error.message, messagesContainer);
            } else {
                alert("Erro ao enviar email de verificação: " + error.message);
            }
        }
    }

    // Atualiza status de verificação
    async function refreshVerificationStatus(user) {
        const refreshBtn = document.getElementById('refresh-verification-btn');
        const originalText = refreshBtn.innerHTML;
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        
        try {
            await loadEmailVerificationStatus(user);
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess("Status atualizado!", messagesContainer, 2000);
            } else {
                alert("Status atualizado!");
            }
        } catch (error) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro ao atualizar status: " + error.message, messagesContainer);
            } else {
                alert("Erro ao atualizar status: " + error.message);
            }
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = originalText;
        }
    }

    // Alterna formulário de alteração de senha
    function toggleChangePasswordForm() {
        const form = document.getElementById('change-password-form');
        const btn = document.getElementById('change-password-btn');
        
        if (form.style.display === 'none') {
            form.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-times"></i> Cancelar';
        } else {
            form.style.display = 'none';
            form.reset();
            btn.innerHTML = '<i class="fas fa-edit"></i> Alterar Senha';
        }
    }

    // Salva nova senha
    async function saveNewPassword(user) {
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        // Validações
        if (!currentPassword || !newPassword || !confirmPassword) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Por favor, preencha todos os campos.", messagesContainer);
            } else {
                alert("Por favor, preencha todos os campos.");
            }
            return;
        }

        if (newPassword.length < 6) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("A nova senha deve ter pelo menos 6 caracteres.", messagesContainer);
            } else {
                alert("A nova senha deve ter pelo menos 6 caracteres.");
            }
            return;
        }

        if (newPassword !== confirmPassword) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("As senhas não coincidem.", messagesContainer);
            } else {
                alert("As senhas não coincidem.");
            }
            return;
        }

        if (currentPassword === newPassword) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("A nova senha deve ser diferente da senha atual.", messagesContainer);
            } else {
                alert("A nova senha deve ser diferente da senha atual.");
            }
            return;
        }

        try {
            // Reautenticar usuário (necessário para alterar senha no Firebase)
            const credential = EmailAuthProvider.credential(user.email, currentPassword);
            await reauthenticateWithCredential(user, credential);

            // Atualizar senha no Firebase
            await updatePassword(user, newPassword);

            // Notificar backend
            const idToken = await user.getIdToken(true);
            const response = await fetch("/api/auth/change-password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id_token: idToken,
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || "Erro ao alterar senha");
            }

            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess("Senha alterada com sucesso!", messagesContainer, 3000);
            } else {
                alert("Senha alterada com sucesso!");
            }
            toggleChangePasswordForm(); // Fecha o formulário
        } catch (error) {
            console.error("Erro ao alterar senha:", error);
            
            let errorMessage = "Erro ao alterar senha: ";
            if (error.code === 'auth/wrong-password') {
                errorMessage += "Senha atual incorreta.";
            } else if (error.code === 'auth/weak-password') {
                errorMessage += "A nova senha é muito fraca.";
            } else {
                errorMessage += error.message;
            }
            
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError(errorMessage, messagesContainer);
            } else {
                alert(errorMessage);
            }
        }
    }

    // Event listeners para segurança
    document.getElementById('resend-verification-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await resendVerificationEmail(user);
        }
    });

    document.getElementById('refresh-verification-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await refreshVerificationStatus(user);
        }
    });

    document.getElementById('change-password-btn')?.addEventListener('click', toggleChangePasswordForm);
    document.getElementById('cancel-password-btn')?.addEventListener('click', toggleChangePasswordForm);
    document.getElementById('save-password-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await saveNewPassword(user);
        }
    });

    // Carrega status de verificação quando o usuário estiver logado
    onAuthStateChanged(auth, async (user) => {
        if (user) {
            await loadEmailVerificationStatus(user);
            await loadMFAStatus(user);
        }
    });

    // --- Funções de 2FA (Verificação em Duas Etapas) ---
    
    let mfaSecret = null; // Armazena secret temporário durante setup
    
    // Carrega status de 2FA
    async function loadMFAStatus(user) {
        try {
            const idToken = await user.getIdToken();
            
            const response = await fetch("/api/auth/mfa/status", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id_token: idToken })
            });

            if (!response.ok) {
                // Se não for admin, não mostrar seção 2FA
                const mfaSection = document.getElementById('mfa-section');
                if (mfaSection) mfaSection.style.display = 'none';
                return;
            }

            const data = await response.json();
            const mfaSection = document.getElementById('mfa-section');
            const statusText = document.getElementById('mfa-status-text');
            const enableBtn = document.getElementById('enable-mfa-btn');
            const disableBtn = document.getElementById('disable-mfa-btn');

            if (!mfaSection || !data.is_admin) {
                if (mfaSection) mfaSection.style.display = 'none';
                return;
            }

            // Mostrar seção apenas para admins
            mfaSection.style.display = 'flex';

            if (data.mfa_enabled) {
                statusText.innerHTML = '<span class="email-verified"><i class="fas fa-check-circle"></i> 2FA habilitado</span>';
                enableBtn.style.display = 'none';
                disableBtn.style.display = 'inline-flex';
            } else {
                statusText.innerHTML = '<span class="email-unverified"><i class="fas fa-exclamation-circle"></i> 2FA não habilitado</span>';
                enableBtn.style.display = 'inline-flex';
                disableBtn.style.display = 'none';
            }
        } catch (error) {
            console.error("Erro ao carregar status 2FA:", error);
            const mfaSection = document.getElementById('mfa-section');
            if (mfaSection) mfaSection.style.display = 'none';
        }
    }

    // Iniciar setup de 2FA
    async function setupMFA(user) {
        try {
            const idToken = await user.getIdToken();
            
            const response = await fetch("/api/auth/mfa/setup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ id_token: idToken })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || "Erro ao configurar 2FA");
            }

            const data = await response.json();
            mfaSecret = data.secret; // Armazenar secret temporariamente
            
            // Mostrar QR code
            document.getElementById('mfa-qr-code').src = data.qr_code;
            document.getElementById('mfa-manual-key').value = data.manual_entry_key;
            
            // Mostrar formulário de setup
            document.getElementById('mfa-setup-form').style.display = 'block';
            document.getElementById('enable-mfa-btn').style.display = 'none';
            
        } catch (error) {
            console.error("Erro ao configurar 2FA:", error);
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro ao configurar 2FA: " + error.message, messagesContainer);
            } else {
                alert("Erro ao configurar 2FA: " + error.message);
            }
        }
    }

    // Confirmar e habilitar 2FA
    async function confirmEnableMFA(user) {
        const code = document.getElementById('mfa-verify-code').value;
        
        if (!code || code.length !== 6) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Por favor, digite o código de 6 dígitos do seu app autenticador.", messagesContainer);
            } else {
                alert("Por favor, digite o código de 6 dígitos do seu app autenticador.");
            }
            return;
        }

        if (!mfaSecret) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro: Secret não encontrado. Por favor, inicie o setup novamente.", messagesContainer);
            } else {
                alert("Erro: Secret não encontrado. Por favor, inicie o setup novamente.");
            }
            return;
        }

        try {
            const idToken = await user.getIdToken();
            
            const response = await fetch("/api/auth/mfa/enable", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id_token: idToken,
                    secret: mfaSecret,
                    code: code
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || "Erro ao habilitar 2FA");
            }

            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess("2FA habilitado com sucesso!", messagesContainer, 3000);
            } else {
                alert("2FA habilitado com sucesso!");
            }
            
            // Limpar formulário
            document.getElementById('mfa-setup-form').style.display = 'none';
            document.getElementById('mfa-verify-code').value = '';
            mfaSecret = null;
            
            // Recarregar status
            await loadMFAStatus(user);
            
        } catch (error) {
            console.error("Erro ao habilitar 2FA:", error);
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro ao habilitar 2FA: " + error.message, messagesContainer);
            } else {
                alert("Erro ao habilitar 2FA: " + error.message);
            }
        }
    }

    // Desabilitar 2FA
    async function disableMFA(user) {
        const code = document.getElementById('mfa-disable-code').value;
        
        if (!code || code.length !== 6) {
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Por favor, digite o código de 6 dígitos do seu app autenticador para confirmar.", messagesContainer);
            } else {
                alert("Por favor, digite o código de 6 dígitos do seu app autenticador para confirmar.");
            }
            return;
        }

        try {
            const idToken = await user.getIdToken();
            
            const response = await fetch("/api/auth/mfa/disable", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id_token: idToken,
                    code: code
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || "Erro ao desabilitar 2FA");
            }

            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess("2FA desabilitado com sucesso!", messagesContainer, 3000);
            } else {
                alert("2FA desabilitado com sucesso!");
            }
            
            // Limpar formulário
            document.getElementById('mfa-disable-form').style.display = 'none';
            document.getElementById('mfa-disable-code').value = '';
            
            // Recarregar status
            await loadMFAStatus(user);
            
        } catch (error) {
            console.error("Erro ao desabilitar 2FA:", error);
            const messagesContainer = document.getElementById('profile-messages-container');
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError("Erro ao desabilitar 2FA: " + error.message, messagesContainer);
            } else {
                alert("Erro ao desabilitar 2FA: " + error.message);
            }
        }
    }

    // Event listeners para 2FA
    document.getElementById('enable-mfa-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await setupMFA(user);
        }
    });

    document.getElementById('disable-mfa-btn')?.addEventListener('click', () => {
        document.getElementById('mfa-disable-form').style.display = 'block';
        document.getElementById('disable-mfa-btn').style.display = 'none';
    });

    document.getElementById('cancel-mfa-setup-btn')?.addEventListener('click', () => {
        document.getElementById('mfa-setup-form').style.display = 'none';
        document.getElementById('mfa-verify-code').value = '';
        mfaSecret = null;
        const user = auth.currentUser;
        if (user) loadMFAStatus(user);
    });

    document.getElementById('cancel-mfa-disable-btn')?.addEventListener('click', () => {
        document.getElementById('mfa-disable-form').style.display = 'none';
        document.getElementById('mfa-disable-code').value = '';
        const user = auth.currentUser;
        if (user) loadMFAStatus(user);
    });

    document.getElementById('confirm-mfa-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await confirmEnableMFA(user);
        }
    });

    document.getElementById('confirm-disable-mfa-btn')?.addEventListener('click', async () => {
        const user = auth.currentUser;
        if (user) {
            await disableMFA(user);
        }
    });
});
