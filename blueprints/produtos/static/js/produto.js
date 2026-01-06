// static/js/produto_detalhes.js

// Funções para controlar a tela de carregamento
function showLoadingScreen() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('hidden');
    } else {
        console.error("Erro: Elemento #loading-overlay não encontrado.");
    }
}

function hideLoadingScreen() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
}

async function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };

    let sessionId = localStorage.getItem('cartSessionId');
    if (!sessionId) {
        sessionId = crypto.randomUUID(); // Gerar um novo UUID se não existir
        localStorage.setItem('cartSessionId', sessionId);
    }
    headers['X-Session-ID'] = sessionId;
    
    // Adicionar token Firebase se disponível
    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
        const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
        
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
        const auth = getAuth(app);
        
        const user = auth.currentUser;
        if (user) {
            const idToken = await user.getIdToken();
            headers['Authorization'] = `Bearer ${idToken}`;
        }
    } catch (error) {
        // Firebase não disponível ou usuário não logado
        console.log('Firebase não disponível ou usuário não logado');
    }
    
    return headers;
}
// ===========

document.addEventListener('DOMContentLoaded', async function() {
    const urlSegments = window.location.pathname.split('/');
    const nomeProdutoId = urlSegments[urlSegments.length - 1];

    let productData = null;
    let selectedEstampa = null;
    let selectedTamanho = null;
    let selectedVariation = null;

    // Referências aos elementos HTML da página
    const productNameElem = document.getElementById('product-name');
    const productDescElem = document.getElementById('product-description');
    const productCategoryElem = document.getElementById('product-category');
    const productPriceElem = document.getElementById('product-price');
    const productImageGallery = document.getElementById('product-image-gallery');
    const estampaOptionsContainer = document.getElementById('estampa-options-container');
    const tamanhoOptionsContainer = document.getElementById('tamanho-options-container');
    const quantityInput = document.getElementById('quantity-input');
    const quantityMinusBtn = document.getElementById('quantity-minus-btn');
    const quantityPlusBtn = document.getElementById('quantity-plus-btn');
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    const stockStatusElem = document.getElementById('stock-status');
    const skuElem = document.getElementById('product-sku');
    const productCategoryBreadcrumb = document.getElementById('product-category-breadcrumb');
    const productNameBreadcrumb = document.getElementById('product-name-breadcrumb');
    const productCategoryInfo = document.getElementById('product-category-info');
    const productTagsElem = document.getElementById('product-tags');
    const oldPriceElem = document.getElementById('old-price');
    const discountBadgeElem = document.getElementById('discount-badge');
    const descriptionTabContent = document.getElementById('description-tab-content');
    const messagesContainer = document.getElementById('product-messages-container');
    
    // Referências aos botões das abas e seus conteúdos
    const tabDescriptionBtn = document.getElementById('tab-description-btn');
    const tabDetailsBtn = document.getElementById('tab-details-btn');
    const tabReviewsBtn = document.getElementById('tab-reviews-btn');
    const descriptionTab = document.getElementById('descriptionTab');
    const detailsTab = document.getElementById('detailsTab');
    const reviewsTab = document.getElementById('reviewsTab');
    const reviewsList = document.getElementById('reviews-list');
    const reviewsCountElem = document.getElementById('reviews-count');
    const writeReviewBtn = document.getElementById('write-review-btn');
    const buyNowBtn = document.getElementById('buy-now-btn');
    
    /**
     * Função auxiliar para mostrar mensagens inline
     */
    function showMessage(message, type = 'info', duration = 5000) {
        if (window.MessageHelper && messagesContainer) {
            return MessageHelper.showMessage(message, type, messagesContainer, duration);
        } else {
            // Fallback se MessageHelper não estiver disponível
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }


    /**
     * Função assíncrona para buscar os detalhes do produto do backend.
     */
    async function fetchProductDetails() {

        try {
            const response = await fetch(`/api/base_products/${nomeProdutoId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    const errorContainer = document.getElementById('main-product-container') || document.body;
                    errorContainer.innerHTML = `
                        <div style="text-align: center; padding: 50px;">
                            <h2>Ops! Produto não encontrado :(</h2>
                            <p>Parece que o produto que você está procurando não existe ou foi removido.</p>
                            <p><a href="/loja" style="text-decoration: underline; color: #007bff;">Voltar para a Loja</a></p>
                        </div>
                    `;
                    throw new Error(`Product not found: status ${response.status}`);
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            productData = await response.json();
            console.log("Detalhes do produto recebidos:", productData);

            // Preenche as informações básicas do produto na página
            productNameElem.textContent = productData.nome;
            productDescElem.textContent = productData.descricao;
            productCategoryElem.textContent = productData.categoria;

            productCategoryBreadcrumb.textContent = productData.categoria;
            productNameBreadcrumb.textContent = productData.nome;
            productCategoryInfo.textContent = productData.categoria;
            descriptionTabContent.innerHTML = productData.descricao; // Para a aba de descrição

            // Popula os seletores de estampa e tamanho com base nas variações disponíveis
            populateVariationSelectors(productData.variations);

            // Preencher detalhes adicionais (abas) - MOCADO por enquanto, para combinar com o HTML original
            // Você precisaria de mais dados no backend para preencher isso dinamicamente
            // e alterar a API get_product_details para retornar esses campos
            document.getElementById('detail-material').textContent = 'Algodão 100%';
            document.getElementById('detail-cor').textContent = 'Varia conforme o modelo';
            document.getElementById('detail-tamanho').textContent = 'P, M, G, GG';
            document.getElementById('detail-peso').textContent = '200g';
            document.getElementById('detail-composicao').textContent = '95% Algodão, 5% Elastano';
            document.getElementById('detail-instrucoes').textContent = 'Lavar na máquina com água fria, não usar alvejante, secar à sombra';

            // Carregar avaliações dinamicamente
            await loadProductReviews(nomeProdutoId);

            // Preencher Tags (mocadas por enquanto)
            const tags = ['lhamas', 'infantil', 'conforto'];
            if (productTagsElem) {
                 productTagsElem.innerHTML = tags.map(tag => `<a href="#" class="tag">${tag}</a>`).join(', ');
            }


        } catch (error) {
            console.error('Erro ao buscar detalhes do produto:', error);
            if (!productData) {
                const errorContainer = document.getElementById('main-product-container') || document.body;
                errorContainer.innerHTML = '<div style="text-align: center; padding: 50px;"><p>Ocorreu um erro ao carregar os detalhes do produto. Tente novamente mais tarde.</p></div>';
            }
        } finally {
        }
    }

    /**
     * Popula os seletores de estampa e tamanho com opções únicas.
     */
    function populateVariationSelectors(variations) {
        // Obter estampas e tamanhos únicos
        const uniqueEstampas = Array.from(new Set(variations.map(v => v.estampa.nome)))
                                    .sort((a, b) => a.localeCompare(b));
        const uniqueTamanhos = Array.from(new Set(variations.map(v => v.tamanho.nome)))
                                     .sort((a, b) => {
                                         const order = {'P': 1, 'M': 2, 'G': 3, 'GG': 4, 'XG': 5};
                                         return (order[a] || 99) - (order[b] || 99);
                                     });

        if (estampaOptionsContainer) estampaOptionsContainer.innerHTML = '';
        if (tamanhoOptionsContainer) tamanhoOptionsContainer.innerHTML = '';

        // Popula as opções de estampa como divs
        uniqueEstampas.forEach(estampaName => {
            const estampaDiv = document.createElement('div');
            estampaDiv.classList.add('color-option');
            estampaDiv.style.backgroundColor = getEstampaColor(estampaName); // Use cores fictícias ou do DB
            estampaDiv.title = estampaName;
            estampaDiv.dataset.estampaNome = estampaName;
            estampaDiv.addEventListener('click', () => {
                selectOption(estampaOptionsContainer, estampaDiv, 'estampa', estampaName);
            });
            if (estampaOptionsContainer) estampaOptionsContainer.appendChild(estampaDiv);
        });

        // Popula as opções de tamanho como divs
        uniqueTamanhos.forEach(tamanhoName => {
            const tamanhoDiv = document.createElement('div');
            tamanhoDiv.classList.add('size-option');
            tamanhoDiv.textContent = tamanhoName;
            tamanhoDiv.dataset.tamanhoNome = tamanhoName;
            tamanhoDiv.addEventListener('click', () => {
                selectOption(tamanhoOptionsContainer, tamanhoDiv, 'tamanho', tamanhoName);
            });
            if (tamanhoOptionsContainer) tamanhoOptionsContainer.appendChild(tamanhoDiv);
        });

        // Seleciona a primeira estampa e o primeiro tamanho como padrão
        if (uniqueEstampas.length > 0 && estampaOptionsContainer.firstElementChild) {
            selectOption(estampaOptionsContainer, estampaOptionsContainer.firstElementChild, 'estampa', uniqueEstampas[0]);
        }
        if (uniqueTamanhos.length > 0 && tamanhoOptionsContainer.firstElementChild) {
            selectOption(tamanhoOptionsContainer, tamanhoOptionsContainer.firstElementChild, 'tamanho', uniqueTamanhos[0]);
        }
    }

    /**
     * Helper para obter uma cor fictícia baseada no nome da estampa.
     * SUBSTITUA ISSO PELA URL REAL DA IMAGEM DA ESTAMPA OU CÓDIGO DE COR SE DISPONÍVEL NO DB.
     */
    function getEstampaColor(estampaName) {
        const colors = {
            'Lhama Feliz': '#90EE90',
            'Banana Estilosa': '#FFD700',
            'Floral Encantado': '#FFB6C1',
            'Astronauta Aventureiro': '#A9A9A9',
            'Dinossauro Radical': '#8B4513'
        };
        return colors[estampaName] || '#CCCCCC';
    }


    /**
     * Função para gerenciar a seleção de opções (estampa/tamanho).
     */
    function selectOption(container, selectedElement, type, value) {
        if (!container) return; // Garante que o contêiner exista

        Array.from(container.children).forEach(el => el.classList.remove('selected'));
        selectedElement.classList.add('selected');

        if (type === 'estampa') {
            selectedEstampa = value;
        } else if (type === 'tamanho') {
            selectedTamanho = value;
        }
        updateProductSelection();
    }

    /**
     * Atualiza a variação selecionada quando o usuário muda as opções.
     */
    function updateProductSelection() {
        if (!selectedEstampa || !selectedTamanho || !productData) {
            return;
        }

        const foundVariation = productData.variations.find(v =>
            v.estampa.nome === selectedEstampa && v.tamanho.nome === selectedTamanho
        );

        if (foundVariation) {
            updateSelectedVariation(foundVariation);
        } else {
            productPriceElem.textContent = 'R$ N/A';
            oldPriceElem.style.display = 'none';
            discountBadgeElem.style.display = 'none';
            stockStatusElem.textContent = 'Combinação indisponível.';
            skuElem.textContent = '-';
            if (addToCartBtn) addToCartBtn.disabled = true;
            if (buyNowBtn) buyNowBtn.disabled = true;
            quantityInput.value = 0;
            quantityInput.max = 0;
            if (productImageGallery) productImageGallery.innerHTML = '<p>Esta combinação não está disponível.</p>';
        }
    }

    /**
     * Atualiza a interface do usuário com os detalhes da variação selecionada.
     */
    function updateSelectedVariation(variation) {
        selectedVariation = variation;

        productPriceElem.textContent = `R$ ${variation.preco.toFixed(2).replace('.', ',')}`;
        oldPriceElem.style.display = 'none';
        discountBadgeElem.style.display = 'none';
        // Você pode implementar a lógica de preço antigo/desconto aqui se tiver esses dados no backend

        skuElem.textContent = variation.sku || '-';
        
        // Resetar quantidade para 1 quando mudar variação
        if (quantityInput) {
        quantityInput.value = 1;
            quantityInput.min = 1;
        }

        if (variation.estoque > 0) {
            stockStatusElem.textContent = `Em estoque: ${variation.estoque} unidades.`;
            if (addToCartBtn) {
                addToCartBtn.textContent = 'Adicionar ao Carrinho';
                addToCartBtn.disabled = false;
            }
            if (buyNowBtn) buyNowBtn.disabled = false;
            if (quantityInput) {
            quantityInput.max = variation.estoque;
                quantityInput.disabled = false;
            }
        } else {
            stockStatusElem.textContent = 'Esgotado.';
            if (addToCartBtn) {
                addToCartBtn.textContent = 'Indisponível';
                addToCartBtn.disabled = true;
            }
            if (buyNowBtn) buyNowBtn.disabled = true;
            if (quantityInput) {
            quantityInput.max = 0;
                quantityInput.value = 0;
                quantityInput.disabled = true;
            }
        }

        // Atualiza a galeria de imagens
        if (productImageGallery) productImageGallery.innerHTML = '';
        const mainImageContainer = document.createElement('div');
        mainImageContainer.classList.add('product-main-image-container');
        const thumbnailsContainer = document.createElement('div');
        thumbnailsContainer.classList.add('product-thumbnails');

        if (variation.images && variation.images.length > 0) {
            const mainImg = document.createElement('img');
            mainImg.src = variation.images[0].url;
            mainImg.alt = variation.images[0].descricao || `${productData.nome} - ${variation.estampa.nome} - ${variation.tamanho.nome}`;
            mainImg.classList.add('product-main-image');
            mainImg.id = 'mainImage';
            mainImageContainer.appendChild(mainImg);
            
            variation.images.forEach((img, index) => {
                const thumbImg = document.createElement('img');
                thumbImg.src = img.url;
                thumbImg.alt = img.descricao || `Miniatura ${index + 1}`;
                thumbImg.classList.add('thumbnail');
                if (index === 0) {
                    thumbImg.classList.add('active');
                }
                thumbImg.addEventListener('click', () => {
                    document.getElementById('mainImage').src = thumbImg.src;
                    Array.from(thumbnailsContainer.children).forEach(t => t.classList.remove('active'));
                    thumbImg.classList.add('active');
                });
                thumbnailsContainer.appendChild(thumbImg);
            });
            if (productImageGallery) {
                productImageGallery.appendChild(mainImageContainer);
                productImageGallery.appendChild(thumbnailsContainer);
            }

        } else {
            if (productImageGallery) {
                productImageGallery.innerHTML = '<p>Nenhuma imagem disponível para esta variação.</p>';
                const placeholderImg = document.createElement('img');
                placeholderImg.src = '/static/img/placeholder.jpg';
                placeholderImg.alt = 'Imagem Indisponível';
                placeholderImg.classList.add('product-main-image');
                mainImageContainer.appendChild(placeholderImg);
                productImageGallery.appendChild(mainImageContainer);
            }
        }
    }

    // --- Lógica de Quantidade ---
    if (quantityMinusBtn) {
        quantityMinusBtn.addEventListener('click', () => {
            let currentValue = parseInt(quantityInput.value) || 1;
            const min = parseInt(quantityInput.min) || 1;
            if (currentValue > min) {
                quantityInput.value = currentValue - 1;
            } else {
                quantityInput.value = min;
            }
        });
    }

    if (quantityPlusBtn) {
        quantityPlusBtn.addEventListener('click', () => {
            let currentValue = parseInt(quantityInput.value) || 1;
            const max = parseInt(quantityInput.max) || 999;
            if (currentValue < max) {
                quantityInput.value = currentValue + 1;
            } else {
                quantityInput.value = max;
                if (selectedVariation && currentValue >= selectedVariation.estoque) {
                    showMessage(`Quantidade máxima disponível: ${selectedVariation.estoque}`, 'warning');
                }
            }
        });
    }
    
    // Validar input de quantidade manualmente
    if (quantityInput) {
        quantityInput.addEventListener('input', () => {
            let value = parseInt(quantityInput.value);
            const min = parseInt(quantityInput.min) || 1;
            const max = parseInt(quantityInput.max) || 999;
            
            if (isNaN(value) || value < min) {
                quantityInput.value = min;
            } else if (value > max) {
                quantityInput.value = max;
                if (selectedVariation) {
                    showMessage(`Quantidade máxima disponível: ${selectedVariation.estoque}`, 'warning');
                }
            }
        });
        
        quantityInput.addEventListener('blur', () => {
            let value = parseInt(quantityInput.value);
            const min = parseInt(quantityInput.min) || 1;
            const max = parseInt(quantityInput.max) || 999;
            
            if (isNaN(value) || value < min) {
                quantityInput.value = min;
            } else if (value > max) {
                quantityInput.value = max;
            }
        });
    }

    // --- Lógica do Carrinho (Placeholder) ---
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', async () => { // Adicionado 'async' aqui
            if (!selectedVariation) {
                showMessage('Por favor, selecione uma variação do produto.', 'warning');
                return;
            }
            const quantity = parseInt(quantityInput.value);
            if (isNaN(quantity) || quantity <= 0) {
                showMessage('Por favor, insira uma quantidade válida.', 'warning');
                return;
            }
            if (quantity > selectedVariation.estoque) {
                showMessage(`A quantidade desejada excede o estoque disponível (${selectedVariation.estoque}).`, 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/cart/add', {
                    method: 'POST',
                    headers: await getAuthHeaders(), // Usar o helper de headers
                    body: JSON.stringify({
                        product_id: selectedVariation.id, // ID da variação do produto
                        quantity: quantity
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    showMessage(`Erro ao adicionar ao carrinho: ${errorData.erro || 'Ocorreu um erro desconhecido.'}`, 'error');
                    console.error('Erro detalhado:', errorData);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const responseData = await response.json();
                showMessage(responseData.mensagem || 'Item adicionado ao carrinho!', 'success');
                console.log('Item adicionado ao carrinho:', responseData);
                
                // Resetar quantidade para 1 após adicionar (permitindo adicionar novamente)
                if (quantityInput) {
                    quantityInput.value = 1;
                }

                // Opcional: Atualizar algum contador de carrinho no header, etc.
                // Ou redirecionar para o carrinho: window.location.href = '/carrinho';

            } catch (error) {
                console.error('Falha ao adicionar item ao carrinho:', error);
                showMessage('Não foi possível adicionar o item ao carrinho. Tente novamente.', 'error');
            } finally {
            }
        });
    }

    // --- Lógica do Comprar Agora ---
    if (buyNowBtn) {
        buyNowBtn.addEventListener('click', async () => {
            if (!selectedVariation) {
                showMessage('Por favor, selecione uma variação do produto.', 'warning');
                return;
            }
            const quantity = parseInt(quantityInput.value);
            if (isNaN(quantity) || quantity <= 0) {
                showMessage('Por favor, insira uma quantidade válida.', 'warning');
                return;
            }
            if (quantity > selectedVariation.estoque) {
                showMessage(`A quantidade desejada excede o estoque disponível (${selectedVariation.estoque}).`, 'error');
                return;
            }
            
            // Salvar texto original do botão antes de desabilitar
            const originalText = buyNowBtn.innerHTML;
            
            try {
                // Desabilitar botão durante a requisição
                buyNowBtn.disabled = true;
                buyNowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adicionando...';
                
                const response = await fetch('/api/cart/add', {
                    method: 'POST',
                    headers: await getAuthHeaders(),
                    body: JSON.stringify({
                        product_id: selectedVariation.id, // ID da variação do produto
                        quantity: quantity
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    showMessage(`Erro ao adicionar ao carrinho: ${errorData.erro || 'Ocorreu um erro desconhecido.'}`, 'error');
                    console.error('Erro detalhado:', errorData);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const responseData = await response.json();
                showMessage('Item adicionado ao carrinho! Redirecionando...', 'success');
                console.log('Item adicionado ao carrinho:', responseData);
                
                // Redirecionar para o carrinho após um breve delay
                setTimeout(() => {
                    window.location.href = '/carrinho';
                }, 500);

            } catch (error) {
                console.error('Falha ao adicionar item ao carrinho:', error);
                showMessage('Não foi possível adicionar o item ao carrinho. Tente novamente.', 'error');
                // Restaurar botão em caso de erro
                buyNowBtn.disabled = false;
                buyNowBtn.innerHTML = originalText;
            }
        });
    }
    
    // --- Lógica das Abas ---
    const tabButtons = [tabDescriptionBtn, tabDetailsBtn, tabReviewsBtn];
    const tabContents = {
        'description': descriptionTab,
        'details': detailsTab,
        'reviews': reviewsTab
    };
    
    let reviewsLoaded = false; // Flag para evitar carregar múltiplas vezes

    tabButtons.forEach(button => {
        if (button) { // Garante que o botão existe
            button.addEventListener('click', async function() {
                tabButtons.forEach(btn => { if (btn) btn.classList.remove('active'); });
                Object.values(tabContents).forEach(content => { if (content) content.style.display = 'none'; });

                this.classList.add('active');
                const targetTab = this.getAttribute('data-tab');
                if (tabContents[targetTab]) tabContents[targetTab].style.display = 'block';
                
                // Carregar avaliações quando a aba de reviews for aberta
                if (targetTab === 'reviews' && !reviewsLoaded && productData) {
                    reviewsLoaded = true;
                    await loadProductReviews(nomeProdutoId);
                }
            });
        }
    });

    /**
     * Carrega avaliações do produto do backend
     */
    async function loadProductReviews(productId) {
        try {
            const response = await fetch(`/api/base_products/${productId}/reviews`);
            if (!response.ok) {
                throw new Error('Erro ao carregar avaliações');
            }
            
            const data = await response.json();
            renderReviews(data.reviews || [], data.stats || {});
            
            // Atualizar contador
            if (reviewsCountElem) {
                reviewsCountElem.textContent = data.stats?.total || 0;
            }
            
            // Carregar avaliação do usuário logado
            await loadMyReview(productId);
        } catch (error) {
            console.error('Erro ao carregar avaliações:', error);
            if (reviewsList) {
                reviewsList.innerHTML = '<p>Erro ao carregar avaliações. Tente novamente mais tarde.</p>';
            }
        }
    }
    
    /**
     * Carrega a avaliação do usuário logado
     */
    async function loadMyReview(productId) {
        try {
            const headers = await getAuthHeaders();
            const response = await fetch(`/api/base_products/${productId}/reviews/me`, {
                headers: headers
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.review) {
                    // Usuário já avaliou, mostrar opção de editar
                    showEditReviewForm(data.review);
                } else {
                    // Usuário não avaliou, mostrar formulário de nova avaliação
                    showNewReviewForm();
                }
            } else {
                showNewReviewForm();
            }
        } catch (error) {
            console.error('Erro ao carregar minha avaliação:', error);
            showNewReviewForm();
        }
    }
    
    /**
     * Renderiza as avaliações na lista
     */
    function renderReviews(reviews, stats) {
        if (reviewsList) reviewsList.innerHTML = '';
        
        if (reviews && reviews.length > 0) {
            // Mostrar estatísticas se disponíveis
            if (stats && stats.total > 0) {
                const statsHtml = `
                    <div class="reviews-stats">
                        <div class="stats-main">
                            <div class="stats-rating">
                                ${stats.media ? stats.media.toFixed(1) : '0.0'}
                            </div>
                            <div class="stats-info">
                                <div class="stats-stars">
                                    ${renderStars(stats.media || 0)}
                                </div>
                                <div class="stats-count">
                                    ${stats.total} ${stats.total === 1 ? 'avaliação' : 'avaliações'}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                reviewsList.innerHTML = statsHtml;
            }
            
            reviews.forEach(review => {
                const reviewDiv = document.createElement('div');
                reviewDiv.classList.add('review');
                reviewDiv.innerHTML = `
                    <div class="review-header">
                        <span class="review-author">${review.usuario_nome}</span>
                        <div class="review-rating">
                            ${renderStars(review.rating)}
                        </div>
                        <span class="review-date">${review.criado_em}</span>
                    </div>
                    ${review.comentario ? `<p class="review-text">${review.comentario}</p>` : ''}
                `;
                if (reviewsList) reviewsList.appendChild(reviewDiv);
            });
        } else {
            if (reviewsList) {
                reviewsList.innerHTML = '<p>Nenhuma avaliação ainda. Seja o primeiro a avaliar!</p>';
            }
        }
    }
    
    /**
     * Renderiza estrelas baseado na nota
     */
    function renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let html = '';
        
        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star"></i>';
        }
        
        if (hasHalfStar && fullStars < 5) {
            html += '<i class="fas fa-star-half-alt"></i>';
        }
        
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star"></i>';
        }
        
        return html;
    }
    
    /**
     * Mostra formulário de nova avaliação
     */
    function showNewReviewForm() {
        if (!writeReviewBtn) return;
        
        writeReviewBtn.style.display = 'block';
        writeReviewBtn.onclick = () => {
            showReviewModal();
        };
    }
    
    /**
     * Mostra formulário de edição de avaliação
     */
    function showEditReviewForm(review) {
        if (!writeReviewBtn) return;
        
        writeReviewBtn.style.display = 'block';
        writeReviewBtn.textContent = 'Editar minha avaliação';
        writeReviewBtn.onclick = () => {
            showReviewModal(review);
        };
    }
    
    /**
     * Mostra modal de avaliação
     */
    function showReviewModal(existingReview = null) {
        const modal = document.createElement('div');
        modal.className = 'review-modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'review-modal-content';
        
        let selectedRating = existingReview ? existingReview.rating : 0;
        
        modalContent.innerHTML = `
            <h2>${existingReview ? 'Editar Avaliação' : 'Escrever Avaliação'}</h2>
            <div>
                <label>Sua avaliação:</label>
                <div class="rating-input">
                    ${[1,2,3,4,5].map(i => `
                        <i class="${i <= selectedRating ? 'fas' : 'far'} fa-star star-rating" data-rating="${i}"></i>
                    `).join('')}
                </div>
            </div>
            <div>
                <label>Comentário (opcional):</label>
                <textarea id="review-comment" rows="4">${existingReview ? (existingReview.comentario || '') : ''}</textarea>
            </div>
            <div class="review-modal-actions">
                <button class="btn-cancel-review">Cancelar</button>
                <button class="btn-submit-review">${existingReview ? 'Atualizar' : 'Enviar'}</button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // Event listeners para estrelas
        const stars = modalContent.querySelectorAll('.star-rating');
        const updateStars = (rating) => {
            stars.forEach((s, i) => {
                s.className = i < rating ? 'fas fa-star star-rating' : 'far fa-star star-rating';
                s.dataset.rating = i + 1;
            });
        };
        
        stars.forEach(star => {
            star.addEventListener('click', () => {
                selectedRating = parseInt(star.dataset.rating);
                updateStars(selectedRating);
            });
            
            star.addEventListener('mouseenter', () => {
                const hoverRating = parseInt(star.dataset.rating);
                updateStars(hoverRating);
            });
        });
        
        const ratingInput = modalContent.querySelector('.rating-input');
        ratingInput.addEventListener('mouseleave', () => {
            updateStars(selectedRating);
        });
        
        // Event listeners para botões
        modalContent.querySelector('.btn-cancel-review').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modalContent.querySelector('.btn-submit-review').addEventListener('click', async () => {
            if (selectedRating === 0) {
                showMessage('Por favor, selecione uma avaliação de 1 a 5 estrelas.', 'warning');
                return;
            }
            
            const comment = modalContent.querySelector('#review-comment').value.trim();
            
            try {
                const headers = await getAuthHeaders();
                if (!headers['Authorization']) {
                    showMessage('Você precisa estar logado para fazer uma avaliação.', 'warning');
                    document.body.removeChild(modal);
                    return;
                }
                
                const response = await fetch(`/api/base_products/${nomeProdutoId}/reviews`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({
                        rating: selectedRating,
                        comentario: comment
                    })
                });
                
                if (response.ok) {
                    document.body.removeChild(modal);
                    await loadProductReviews(nomeProdutoId);
                    showMessage('Avaliação salva com sucesso!', 'success');
                } else {
                    const error = await response.json();
                    showMessage(error.erro || 'Erro ao salvar avaliação.', 'error');
                }
            } catch (error) {
                console.error('Erro ao salvar avaliação:', error);
                showMessage('Erro ao salvar avaliação. Tente novamente.', 'error');
            }
        });
        
        // Fechar ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    // Inicializar botão de escrever avaliação
    if (writeReviewBtn) {
        writeReviewBtn.style.display = 'none'; // Esconder até carregar avaliações
    }

    // Inicia o processo de busca e renderização dos detalhes do produto
    fetchProductDetails();
});